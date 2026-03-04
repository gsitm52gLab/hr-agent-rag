import json
import time
from typing import AsyncGenerator

import httpx

import config
from services.embedding import get_embedding
from services.vector_store import search, keyword_search
from services.db import get_conn


# Query keyword → employee role search keywords (user's question → direct role match)
_QUERY_ROLE_MAP = {
    "경비": ["경비", "비용", "회계"],
    "비용": ["경비", "비용", "회계"],
    "정산": ["경비정산", "정산"],
    "회계": ["회계", "전표"],
    "세금": ["세무", "법인세", "부가세"],
    "세무": ["세무", "법인세", "부가세"],
    "예산": ["예산"],
    "결산": ["결산", "재무"],
    "자금": ["자금"],
    "재무": ["재무", "결산", "회계"],
    "전표": ["전표", "회계"],
    "구매": ["구매", "발주"],
    "발주": ["발주", "구매"],
    "계약": ["계약"],
    "외주": ["외주", "용역"],
    "입찰": ["입찰", "계약"],
    "자재": ["자재", "구매"],
    "채용": ["채용", "인사기획"],
    "면접": ["채용"],
    "입사": ["채용", "근로계약"],
    "수습": ["수습", "채용"],
    "근로계약": ["근로계약"],
    "급여": ["급여", "4대보험"],
    "월급": ["급여"],
    "보험": ["4대보험"],
    "퇴직": ["퇴직", "급여"],
    "퇴직금": ["퇴직", "급여"],
    "휴가": ["휴가", "근태"],
    "연차": ["휴가", "근태"],
    "병가": ["휴가", "근태"],
    "출산": ["휴가"],
    "근태": ["근태", "휴가"],
    "야근": ["급여", "근태"],
    "연장근로": ["급여", "근태"],
    "승진": ["승진", "인사기획"],
    "인사": ["인사기획"],
    "징계": ["인사기획"],
    "교육": ["교육"],
    "훈련": ["교육"],
    "복리후생": ["복리후생", "경조사"],
    "경조사": ["경조사", "복리후생"],
    "복장": ["복장", "총무"],
    "사무실": ["사무환경", "자산"],
    "비품": ["비품", "자산"],
    "보안": ["보안", "안전"],
    "차량": ["차량"],
}

# Document category → employee role keyword mapping (fallback)
_CATEGORY_ROLE_MAP = {
    "채용": ["채용", "인사기획"],
    "근무": ["근태", "휴가"],
    "휴가": ["휴가", "근태"],
    "급여": ["급여", "4대보험"],
    "퇴직": ["퇴직", "급여"],
    "징계": ["인사기획"],
    "승진": ["승진", "인사기획"],
    "복리후생": ["복리후생", "경조사"],
    "복장": ["총무", "복장"],
}


def _find_contacts(query: str, results: list[dict]) -> list[dict]:
    """Find relevant contact persons based on the query keywords and search results."""
    conn = get_conn()

    # Phase 1: Match query keywords directly to employee roles (highest priority)
    query_role_keywords = []
    for kw, role_kws in _QUERY_ROLE_MAP.items():
        if kw in query:
            query_role_keywords.extend(role_kws)

    # Phase 2: Extract document categories from results (fallback)
    doc_role_keywords = []
    for r in results:
        doc = r.get("document", "")
        for cat, role_kws in _CATEGORY_ROLE_MAP.items():
            if cat in doc:
                doc_role_keywords.extend(role_kws)

    # Use query-based keywords first, then document-based as fallback
    role_keywords = list(dict.fromkeys(query_role_keywords)) if query_role_keywords else list(dict.fromkeys(doc_role_keywords))

    if not role_keywords:
        return []

    # Search employees whose role matches any keyword
    contacts = []
    seen_ids = set()
    for kw in role_keywords:
        rows = conn.execute(
            """SELECT e.id, e.name, e.position, e.role, e.email, e.phone, d.name as dept_name
               FROM employees e
               JOIN departments d ON e.department_id = d.id
               WHERE e.role ILIKE ?
               ORDER BY e.is_department_head DESC
               LIMIT 2""",
            [f"%{kw}%"],
        ).fetchall()
        for r in rows:
            if r[0] not in seen_ids:
                seen_ids.add(r[0])
                contacts.append({
                    "name": r[1],
                    "position": r[2],
                    "role": r[3],
                    "email": r[4],
                    "phone": r[5],
                    "department": r[6],
                })

    return contacts[:3]  # Max 3 contacts


_PROMOTION_KEYWORDS = ["승진", "고과", "인사평가", "평가점수", "승진할 수", "승진 가능", "승진 기준", "점수", "합격"]


def _is_promotion_query(query: str) -> bool:
    """Check if the query is related to promotion/evaluation."""
    return any(kw in query for kw in _PROMOTION_KEYWORDS)


def _get_personal_context(employee_id: int) -> str:
    """Fetch personal evaluation, attendance, rewards data for the employee."""
    conn = get_conn()

    # Employee info
    emp = conn.execute(
        """SELECT e.name, e.position, e.role, d.name as dept_name
           FROM employees e JOIN departments d ON e.department_id = d.id
           WHERE e.id = ?""",
        [employee_id],
    ).fetchone()
    if not emp:
        return ""

    parts = [f"\n--- 현재 사용자 정보 ---"]
    parts.append(f"이름: {emp[0]}, 직급: {emp[1]}, 소속: {emp[3]}, 담당: {emp[2]}")

    # Evaluations (last 2 years)
    evals = conn.execute(
        """SELECT year, eval_score, performance_score, career_score, competency_score,
                  training_score, reward_penalty_score, eval_grade
           FROM employee_evaluations WHERE employee_id = ? ORDER BY year DESC LIMIT 2""",
        [employee_id],
    ).fetchall()
    if evals:
        parts.append("\n[인사평가 점수 (최근 2년)]")
        parts.append("| 연도 | 종합점수(100) | 인사평가(40) | 근무경력(20) | 직무역량(20) | 교육이수(10) | 상벌사항(10) | 등급 |")
        parts.append("|------|------------|------------|------------|------------|------------|------------|------|")
        for e in evals:
            parts.append(f"| {e[0]} | {e[1]} | {e[2]} | {e[3]} | {e[4]} | {e[5]} | {e[6]} | {e[7]} |")

    # Attendance
    att = conn.execute(
        """SELECT year, total_work_days, present_days, late_count, early_leave_count,
                  absent_count, annual_leave_used, annual_leave_total, overtime_hours, attendance_rate
           FROM attendance_records WHERE employee_id = ? ORDER BY year DESC LIMIT 2""",
        [employee_id],
    ).fetchall()
    if att:
        parts.append("\n[근태 현황]")
        parts.append("| 연도 | 총근무일 | 출근일 | 지각 | 조퇴 | 결근 | 연차사용/총연차 | 초과근무(시간) | 출근율 |")
        parts.append("|------|---------|--------|------|------|------|--------------|-------------|--------|")
        for a in att:
            parts.append(f"| {a[0]} | {a[1]} | {a[2]} | {a[3]} | {a[4]} | {a[5]} | {a[6]}/{a[7]} | {a[8]} | {a[9]}% |")

    # Rewards/Penalties
    rps = conn.execute(
        """SELECT year, type, category, description, date
           FROM rewards_penalties WHERE employee_id = ? ORDER BY year DESC, date DESC""",
        [employee_id],
    ).fetchall()
    if rps:
        parts.append("\n[상벌 이력]")
        for rp in rps:
            parts.append(f"- {rp[0]}년 [{rp[1]}] {rp[2]}: {rp[3]} ({rp[4]})")

    # Promotion history (company-wide stats)
    current_position = emp[1]  # e.g. "대리"
    promo_stats = conn.execute(
        """SELECT year, position_from, position_to, eligible_count, promoted_count, avg_eval_score, min_eval_score
           FROM promotion_history WHERE position_from = ? ORDER BY year DESC""",
        [current_position],
    ).fetchall()
    if promo_stats:
        parts.append(f"\n[회사 전체 승진 현황 - {current_position} → 다음 직급]")
        parts.append("| 연도 | 승진구간 | 대상자 | 승진자 | 승진율 | 합격평균점수 | 합격최저점수 |")
        parts.append("|------|---------|--------|--------|--------|-----------|-----------|")
        for ps in promo_stats:
            rate = round(ps[4] / ps[3] * 100, 1) if ps[3] > 0 else 0
            parts.append(f"| {ps[0]} | {ps[1]}→{ps[2]} | {ps[3]}명 | {ps[4]}명 | {rate}% | {ps[5]} | {ps[6]} |")

    return "\n".join(parts)


def _get_promotion_chart_data(employee_id: int) -> list[dict]:
    """Get promotion history chart data for the employee's position level."""
    conn = get_conn()

    # Get current position
    emp = conn.execute("SELECT position FROM employees WHERE id = ?", [employee_id]).fetchone()
    if not emp:
        return []

    position = emp[0]

    # Get promotion history for this position level
    rows = conn.execute(
        """SELECT year, position_from, position_to, eligible_count, promoted_count, avg_eval_score, min_eval_score
           FROM promotion_history WHERE position_from = ? ORDER BY year ASC""",
        [position],
    ).fetchall()

    # Get user's eval scores by year
    user_evals = {}
    eval_rows = conn.execute(
        "SELECT year, eval_score FROM employee_evaluations WHERE employee_id = ? ORDER BY year ASC",
        [employee_id],
    ).fetchall()
    for er in eval_rows:
        user_evals[er[0]] = er[1]

    result = []
    for r in rows:
        rate = round(r[4] / r[3] * 100, 1) if r[3] > 0 else 0
        result.append({
            "year": r[0],
            "position_from": r[1],
            "position_to": r[2],
            "eligible": r[3],
            "promoted": r[4],
            "rate": rate,
            "avg_score": r[5],
            "min_score": r[6],
            "my_score": user_evals.get(r[0]),
        })

    return result


SYSTEM_PROMPT = """당신은 회사의 인사규정 전문 AI 어시스턴트입니다.
아래 제공된 인사규정 문서를 참고하여 질문에 상세하고 친절하게 답변하세요.

규칙:
1. 제공된 규정 문서에 근거하여 답변합니다.
2. 규정에 명시되지 않은 내용은 "해당 규정에 명시되어 있지 않습니다"라고 답합니다.
3. 답변 시 관련 조항 번호(예: 제○조)를 반드시 인용합니다.
4. 반드시 한국어로만 답변합니다.
5. 답변은 충분히 상세하게 작성합니다:
   - 해당 규정의 핵심 내용을 빠짐없이 설명합니다.
   - 관련 조건, 기간, 금액, 절차 등 구체적인 정보를 포함합니다.
   - 관련된 다른 규정이 있으면 함께 안내합니다.
   - 예외사항이나 주의할 점이 있으면 알려줍니다.
6. 마크다운 형식을 활용하여 읽기 쉽게 구성합니다 (제목, 목록, 강조 등).
7. 수치 데이터가 있을 때는 반드시 마크다운 표(| 헤더 | ... | 형식)로 정리하여 보여줍니다.
8. 개인 데이터(고과점수, 근태, 상벌 등)가 제공된 경우, 해당 데이터를 분석하여 구체적인 조언을 제공합니다. 점수 데이터는 반드시 표로 정리합니다.

아래는 좋은 답변의 예시입니다:

[질문 예시] 연차 며칠이야?
[답변 예시]
## 연차유급휴가 일수

**제15조(연차유급휴가)**에 따르면:

| 근속기간 | 연차일수 |
|---------|---------|
| 1년 미만 | 매월 1일 (최대 11일) |
| 1년 이상 | 15일 |
| 3년 이상 | 매 2년마다 1일 추가 (최대 25일) |

연차는 1년간 80% 이상 출근한 경우에 부여됩니다. 미사용 연차는 **제16조**에 따라 수당으로 보상받을 수 있습니다.

[질문 예시] 야근하면 돈 더줘?
[답변 예시]
## 연장근로수당

**제22조(연장근로)**에 따르면, 연장근로 시 통상임금의 **50%를 가산**하여 지급합니다.

| 근로 유형 | 가산율 |
|----------|--------|
| 연장근로 (8시간 초과) | 통상임금의 50% |
| 야간근로 (22시~06시) | 통상임금의 50% |
| 휴일근로 | 통상임금의 50% |

연장근로는 1주 12시간을 초과할 수 없으며, 사전에 부서장의 승인이 필요합니다."""


def _get_chat_history(conversation_id: str, max_turns: int = 3) -> list[dict]:
    """Load recent conversation history from DuckDB as LLM message format.
    Returns up to max_turns pairs of user/assistant messages (most recent).
    """
    if not conversation_id:
        return []
    conn = get_conn()
    rows = conn.execute(
        """SELECT role, content FROM messages
           WHERE conversation_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        [conversation_id, max_turns * 2],
    ).fetchall()
    if not rows:
        return []
    # rows are newest-first, reverse to chronological order
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


_CASUAL_PATTERNS = [
    "안녕", "하이", "헬로", "hello", "hi", "hey", "반가",
    "고마워", "감사", "thank", "ㅎㅇ", "ㅎㅎ", "ㅋㅋ",
    "잘자", "좋은 아침", "좋은 하루", "수고",
    "뭐해", "심심", "ㅂㅂ", "바이",
]


def _is_casual(query: str) -> bool:
    """Fast check for obvious casual messages."""
    q = query.strip().lower()
    if len(q) <= 10 and any(p in q for p in _CASUAL_PATTERNS):
        return True
    return False


async def _classify_query(query: str, history: list[dict] = None) -> bool:
    """Use LLM to classify if query is HR/company-work related. Returns True if HR-related."""
    messages = [
        {"role": "system", "content": "당신은 분류기입니다. 대화 맥락을 참고하여 사용자의 최신 메시지가 회사생활, 인사규정, 근무, 급여, 휴가, 채용, 승진, 복리후생, 교육, 징계, 퇴직, 복장 등 회사/업무와 관련된 질문인지 판단하세요. 관련 있으면 YES, 일반 대화(인사, 잡담, 개인적 질문 등)면 NO 만 답하세요."},
    ]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": query})

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{config.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            },
        )
        answer = resp.json().get("message", {}).get("content", "").strip().upper()
        return "YES" in answer


async def _casual_chat(query: str, conversation_id: str = None, history: list[dict] = None) -> AsyncGenerator[str, None]:
    """Simple chat response without RAG for casual/non-HR messages."""
    start_time = time.time()
    full_response = ""
    messages = [
        {"role": "system", "content": "당신은 회사의 친절한 AI 어시스턴트 'HR Agent'입니다. 인사규정 관련 질문이 아닌 일반 대화에 대해 자연스럽고 친근하게 한국어로 답변하세요. 회사 관련 질문이 있으면 언제든 물어보라고 안내해주세요. 답변은 간결하게 합니다."},
    ]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": query})

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{config.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 4096,
                },
            },
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        token = data["message"]["content"]
                        full_response += token
                        yield json.dumps({
                            "type": "token",
                            "content": token,
                        }) + "\n"

    yield json.dumps({
        "type": "sources",
        "sources": [],
        "contacts": [],
        "promotion_stats": [],
    }) + "\n"

    elapsed_ms = int((time.time() - start_time) * 1000)
    yield json.dumps({
        "type": "done",
        "conversation_id": conversation_id,
        "full_response": full_response,
        "response_time_ms": elapsed_ms,
    }) + "\n"


async def rag_query(query: str, conversation_id: str = None) -> AsyncGenerator[str, None]:
    """RAG pipeline: classify → casual chat or embed query → search → generate streaming response."""
    # Load recent conversation history for context
    history = _get_chat_history(conversation_id)

    # Quick casual check, then LLM classification (with history for context)
    if _is_casual(query) or not await _classify_query(query, history):
        async for chunk in _casual_chat(query, conversation_id, history):
            yield chunk
        return

    start_time = time.time()

    # 1. Embed the query
    query_embedding = await get_embedding(query)

    # 2. Hybrid search: vector + keyword
    vector_results = search(query_embedding)
    kw_results = keyword_search(query)

    # Merge: deduplicate by (document, section), keyword matches boost relevance
    seen = set()
    results = []
    # Keyword results first (they matched actual terms in the text)
    for r in kw_results:
        key = (r["document"], r["section"])
        if key not in seen:
            seen.add(key)
            results.append(r)
    # Then vector results
    for r in vector_results:
        key = (r["document"], r["section"])
        if key not in seen:
            seen.add(key)
            results.append(r)
    results = results[: config.VECTOR_TOP_K]

    # 3. Build context from results
    sources = []
    context_parts = []
    for r in results:
        sources.append({
            "document": r["document"],
            "section": r["section"],
            "content": r["text"][:500],
            "score": float(r["_distance"]) if "_distance" in r else 0.0,
        })
        context_parts.append(f"[{r['document']} - {r['section']}]\n{r['text']}")

    context = "\n\n---\n\n".join(context_parts)

    # 4. Build the prompt (inject personal data for promotion queries)
    personal_context = ""
    if _is_promotion_query(query):
        personal_context = _get_personal_context(config.ADMIN_EMPLOYEE_ID)

    prompt = f"""참고 인사규정 문서:

{context}
{personal_context}

---

질문: {query}

위 인사규정을 참고하여 답변해주세요.{' 개인 데이터가 제공되었으므로, 해당 직원의 승진 가능성을 구체적인 수치와 함께 분석해주세요.' if personal_context else ''}"""

    # 5. Stream response from Ollama (with conversation history)
    full_response = ""
    llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        llm_messages.extend(history)
    llm_messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{config.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": config.OLLAMA_MODEL,
                "messages": llm_messages,
                "stream": True,
                "options": {
                    "temperature": 0.4,
                    "top_p": 0.85,
                    "num_ctx": 8192,
                },
            },
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        token = data["message"]["content"]
                        full_response += token
                        yield json.dumps({
                            "type": "token",
                            "content": token,
                        }) + "\n"

    # 6. Find relevant contacts based on search results
    contacts = _find_contacts(query, results)

    # 7. Gather promotion chart data if promotion query
    promotion_stats = []
    if _is_promotion_query(query):
        promotion_stats = _get_promotion_chart_data(config.ADMIN_EMPLOYEE_ID)

    # 8. Yield sources + contacts + promotion_stats at the end
    yield json.dumps({
        "type": "sources",
        "sources": sources,
        "contacts": contacts,
        "promotion_stats": promotion_stats,
    }) + "\n"

    # 8. Record stats
    elapsed_ms = int((time.time() - start_time) * 1000)
    conn = get_conn()
    conn.execute(
        "INSERT INTO search_stats (id, query, response_time_ms, source_count) VALUES (nextval('search_stats_id_seq'), ?, ?, ?)",
        [query, elapsed_ms, len(sources)],
    )
    conn.execute(
        "INSERT INTO search_history (id, query) VALUES (nextval('search_history_id_seq'), ?)",
        [query],
    )

    # 9. Yield done signal with metadata
    yield json.dumps({
        "type": "done",
        "conversation_id": conversation_id,
        "full_response": full_response,
        "response_time_ms": elapsed_ms,
    }) + "\n"
