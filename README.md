# HR Agent RAG System

인사규정 문서 기반 RAG(Retrieval-Augmented Generation) 챗봇 시스템.
사용자가 구어체 한국어로 질문하면, 인사규정에서 관련 조항을 찾아 로컬 LLM이 답변을 생성합니다.

## 목차

- [시스템 구성도](#시스템-구성도)
- [사전 준비 (AI 처음이라면 꼭 읽기)](#사전-준비-ai-처음이라면-꼭-읽기)
- [시작하기](#시작하기)
- [주요 프로세스](#주요-프로세스)
- [API 엔드포인트](#api-엔드포인트)
- [프로젝트 구조](#프로젝트-구조)
- [운영 가이드](#운영-가이드)
- [알려진 한계](#알려진-한계)

---

## 시스템 구성도

```
┌──────────────────────┐      ┌──────────────────────────────────┐
│  Next.js 프론트엔드    │      │  FastAPI 백엔드 (Docker)          │
│  localhost:3000       │◄────►│  localhost:8000                   │
│                       │ REST │                                   │
│  - 채팅 UI            │  API │  - RAG 파이프라인                  │
│  - 관리자 페이지       │      │  - 하이브리드 검색                  │
│  - 자동완성            │      │  - SSE 스트리밍 응답               │
└──────────────────────┘      └────────┬──────────┬───────────────┘
                                       │          │
                              ┌────────▼──┐  ┌───▼────────┐
                              │  LanceDB   │  │  DuckDB     │
                              │  (벡터 DB)  │  │ (관계형 DB)  │
                              └────────────┘  └─────────────┘
                                       │
                              ┌────────▼────────┐
                              │  Ollama (호스트)   │
                              │  localhost:11434  │
                              │                   │
                              │  - exaone3.5:7.8b │  ← LLM (답변 생성)
                              │  - bge-m3         │  ← 임베딩 (벡터 변환)
                              └───────────────────┘
```

---

## 사전 준비 (AI 처음이라면 꼭 읽기)

### 이 시스템이 하는 일

1. 인사규정 문서(마크다운 21개)를 **벡터(숫자 배열)**로 변환하여 DB에 저장
2. 사용자가 질문하면, 질문도 벡터로 변환하여 **가장 유사한 규정 조항을 검색**
3. 검색된 조항을 LLM에게 "이 자료를 참고해서 답변해줘"라고 전달 → **근거 기반 답변 생성**

이것이 RAG(Retrieval-Augmented Generation)입니다. LLM이 학습하지 않은 사내 규정도 정확히 답변할 수 있게 해줍니다.

### 핵심 용어 정리

| 용어 | 설명 |
|------|------|
| **LLM** | 대규모 언어 모델. ChatGPT 같은 AI. 이 프로젝트는 로컬에서 실행되는 `exaone3.5:7.8b` 사용 |
| **Ollama** | LLM을 로컬 PC에서 실행해주는 도구. GPU가 있으면 빠름 |
| **임베딩(Embedding)** | 텍스트를 1024차원 숫자 배열로 변환하는 것. 의미가 비슷한 문장은 숫자도 비슷해짐 |
| **벡터 검색** | 임베딩된 숫자 배열끼리 유사도를 계산하여 가장 관련 높은 문서를 찾는 것 |
| **RAG** | 검색(Retrieval) + 생성(Generation). 문서를 검색한 뒤 LLM이 답변을 만드는 방식 |
| **SSE** | Server-Sent Events. 서버가 응답을 한 글자씩 스트리밍으로 보내는 방식 |
| **LanceDB** | 벡터 전용 DB. 임베딩된 문서 청크를 저장하고 유사도 검색을 수행 |
| **DuckDB** | 경량 관계형 DB. 용어사전, 대화기록, 통계 등 구조화된 데이터를 저장 |

### 하드웨어 요구사항

- **RAM**: 최소 16GB (LLM이 ~5GB 메모리 사용)
- **GPU**: NVIDIA GPU 권장 (없으면 CPU로 실행 가능하나 응답이 매우 느림)
- **디스크**: 약 10GB 여유 공간 (모델 파일 + Docker 이미지)

---

## 시작하기

### 1단계: Ollama 설치 및 모델 다운로드

Ollama는 LLM을 로컬에서 실행하는 도구입니다.

```bash
# 1. Ollama 설치 (https://ollama.com 에서 다운로드)

# 2. 설치 확인
ollama --version

# 3. 모델 다운로드 (최초 1회, 약 5~6GB)
ollama pull exaone3.5:7.8b    # LLM 모델 (답변 생성용)
ollama pull bge-m3             # 임베딩 모델 (텍스트→벡터 변환용)

# 4. 모델 목록 확인
ollama list
# exaone3.5:7.8b, bge-m3 두 개가 보여야 합니다
```

> Ollama는 백그라운드 서비스로 자동 실행됩니다 (localhost:11434).
> 실행 중인지 확인: `curl http://localhost:11434` → "Ollama is running" 응답

### 2단계: 백엔드 실행 (Docker)

```bash
# 1. Docker Desktop이 실행 중인지 확인

# 2. 프로젝트 루트에서 빌드 + 실행
cd D:\workplace\mkagent\case1
docker-compose up --build -d

# 3. 로그 확인 (첫 실행 시 자동 인제스션 ~2분 소요)
docker-compose logs -f backend
```

첫 실행 시 나타나는 로그:
```
[Startup] Data not found. Running auto-ingestion...
[Ingestion] Processing 01_채용규정.md ...
...
[Ingestion] Complete. 21 documents processed.
[Startup] Auto-ingestion complete.
```

> 이 과정에서 인사규정 21개 파일을 읽어 → 임베딩 변환 → LanceDB/DuckDB에 저장합니다.

헬스체크: `curl http://localhost:8000/api/health` → `{"status":"ok"}`

### 3단계: 프론트엔드 실행

```bash
cd D:\workplace\mkagent\case1\frontend

# 최초 1회
npm install

# 개발 서버 시작
npm run dev
```

브라우저에서 `http://localhost:3000` 접속 → 로그인 화면 표시

### 4단계: 로그인 및 사용

| 항목 | 값 |
|------|-----|
| URL | http://localhost:3000/login |
| 아이디 | `admin` |
| 비밀번호 | `admin` |

로그인 후 채팅창에서 인사규정 관련 질문을 입력하면 됩니다.

**예시 질문:**
- "연차 며칠이야?"
- "야근수당 어떻게 계산해?"
- "출장비 얼마까지 나와?"
- "징계 종류 알려줘"

---

## 주요 프로세스

### 1. 데이터 인제스션 (문서 → DB 저장)

시스템 최초 실행 시 또는 데이터가 없을 때 자동 수행됩니다.

```
data/*.md 파일 21개
    │
    ▼
[MD 파싱] 마크다운을 "## " 기준으로 섹션(청크)별 분리
    │
    ▼
[임베딩] 각 청크를 Ollama bge-m3 모델로 1024차원 벡터로 변환
    │
    ├──▶ [LanceDB] 벡터 + 원본텍스트 + 메타데이터 저장 (벡터 검색용)
    │
    └──▶ [DuckDB] 용어사전(glossary_seed.json), 예시질문, 문서 메타 저장
```

### 2. 채팅 (질문 → 답변) - RAG 파이프라인

사용자가 질문을 입력하면 다음 과정을 거칩니다:

```
[사용자 질문] "야근수당 어떻게 계산해?"
    │
    ▼
① [대화 히스토리 로딩] 최근 3턴의 대화 맥락 조회
    │
    ▼
② [질문 분류] LLM이 인사규정 관련 질문인지 판단 (YES/NO)
    │
    ├── NO → 일반 대화로 응답 (RAG 생략)
    │
    ▼ YES
③ [하이브리드 검색] 두 가지 검색을 동시에 수행
    │
    ├── 벡터 검색: 질문을 임베딩 → LanceDB 코사인 유사도 검색
    │     (정식 용어에 강함: "시간외근무수당" 등)
    │
    └── 키워드 검색: 한국어 접미사 제거 + 동의어 확장
          (구어체에 강함: "야근수당" → "시간외근무수당" 매칭)
    │
    ▼
④ [결과 병합] 키워드 결과 우선 배치 + 벡터 결과 추가 (중복 제거, 상위 5개)
    │
    ▼
⑤ [LLM 답변 생성] 검색된 규정 조항을 컨텍스트로 포함하여 Ollama에 전달
    │  - temperature: 0.4 (사실적 답변)
    │  - context window: 8192 토큰
    │
    ▼
⑥ [SSE 스트리밍] 응답을 토큰 단위로 실시간 전송
    │
    ├── {"type":"token", "content":"야근"}     ← 한 글자씩
    ├── {"type":"token", "content":"수당은"}
    ├── {"type":"sources", "sources":[...]}    ← 참고 규정 출처
    └── {"type":"done", "conversation_id":..., "response_time_ms":...}
```

### 3. 하이브리드 검색 상세

순수 벡터 검색만으로는 구어체 한국어("야근수당 얼마야?")를 처리하기 어렵습니다.
이를 보완하기 위해 **벡터 + 키워드** 하이브리드 검색을 사용합니다.

**키워드 검색 흐름:**
```
"야근수당주니?" (사용자 입력)
    │
    ▼ 접미사 제거 (70개+ 한국어 조사/어미 패턴)
"야근수당" (스테밍 결과)
    │
    ▼ 동의어 확장 (DuckDB glossary의 aliases 필드 참조)
"야근수당" → ["시간외근무수당", "초과근무수당", ...] (확장된 검색어)
    │
    ▼ 전체 문서 청크에서 매칭 + 점수 계산
    │  점수 = 매칭_길이×10 + 매칭_횟수 + 섹션제목보너스
    │
    ▼ 상위 5개 반환
```

### 4. 자동완성

입력창에 타이핑 시 3가지 소스에서 추천합니다:

| 트리거 | 소스 | 표시 |
|--------|------|------|
| 1글자 이상 | 최근 검색 이력 | 기본 아이콘 |
| 1글자 이상 | 예시 질문 (question + keywords 매칭) | 파란 `?` 아이콘 |
| 1글자 이상 | 용어사전 (term + aliases 매칭) | 보라 카테고리 라벨 |

### 5. 승진 관련 질문 처리

"승진", "인사평가" 등 키워드가 포함된 질문의 경우:
- 로그인한 사용자의 인사 데이터(평가 점수, 근태, 상벌)를 자동 조회
- 같은 직급의 승진 통계를 차트 데이터로 함께 제공
- 개인화된 답변 생성 ("회원님의 최근 평가 점수는 B+이며...")

---

## API 엔드포인트

### 인증
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/auth/login` | 로그인 → JWT 토큰 발급 |

### 채팅
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/chat` | RAG 질의 (SSE 스트리밍) |
| GET | `/api/chat/history` | 대화 목록 |
| GET | `/api/chat/history/{id}` | 대화 상세 (메시지 포함) |
| DELETE | `/api/chat/history/{id}` | 대화 삭제 |

### 용어사전
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/glossary/search?q=` | 용어 검색 (term + aliases) |
| GET | `/api/glossary` | 전체 목록 |
| POST | `/api/glossary` | 용어 추가 |
| PUT | `/api/glossary/{id}` | 용어 수정 |
| DELETE | `/api/glossary/{id}` | 용어 삭제 |

### 관리자
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/admin/documents` | 문서 목록 |
| POST | `/api/admin/documents` | 문서 추가 |
| PUT | `/api/admin/documents/{id}` | 문서 수정 |
| DELETE | `/api/admin/documents/{id}` | 문서 삭제 |
| POST | `/api/admin/reindex` | 벡터 재인덱싱 |
| GET | `/api/admin/stats` | 검색 통계 |

### 기타
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/history/recent` | 최근 검색어 |
| GET | `/api/history/examples?q=` | 예시 질문 검색 |
| GET | `/api/org/chart` | 조직도 |
| GET | `/api/health` | 헬스체크 |

---

## 프로젝트 구조

```
hr-agent-rag/
├── .gitignore
├── docker-compose.yml              # 백엔드 Docker 설정
├── backend/                         # FastAPI 백엔드
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                      # 앱 진입점 + 자동 인제스션
│   ├── config.py                    # 환경변수 기반 설정
│   ├── auth.py                      # JWT 인증
│   ├── models/
│   │   └── schemas.py               # Pydantic 모델
│   ├── routers/
│   │   ├── auth.py                  # 로그인
│   │   ├── chat.py                  # 채팅 (SSE 스트리밍)
│   │   ├── glossary.py              # 용어사전 CRUD
│   │   ├── history.py               # 검색 이력
│   │   ├── admin.py                 # 문서 관리 + 통계
│   │   └── org.py                   # 조직도
│   ├── services/
│   │   ├── db.py                    # DuckDB 연결 + 스키마
│   │   ├── embedding.py             # Ollama 임베딩 호출
│   │   ├── ingestion.py             # MD 파싱 → 벡터 저장
│   │   ├── rag.py                   # RAG 파이프라인 핵심
│   │   └── vector_store.py          # 하이브리드 검색
│   └── test_search.py               # 검색 품질 테스트
├── frontend/                        # Next.js 프론트엔드
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── src/
│       ├── app/                     # 페이지
│       │   ├── page.tsx             # 메인 채팅
│       │   ├── login/page.tsx       # 로그인
│       │   └── admin/               # 관리자 (통계, 문서, 용어사전, 조직도)
│       ├── components/
│       │   ├── chat/                # ChatInterface, MessageBubble, AutocompleteInput 등
│       │   ├── sidebar/             # Sidebar, ConversationList
│       │   ├── admin/               # DocumentManager, GlossaryEditor, StatsChart
│       │   └── ui/                  # Button, Input, Modal
│       ├── hooks/                   # useChat, useAutocomplete, useAuth
│       └── lib/                     # api.ts, types.ts, auth.ts
└── data/                            # 인사규정 원본 데이터
    ├── 01_채용규정.md ~ 21_윤리경영규정.md
    ├── glossary_seed.json           # 용어사전 초기 데이터 (aliases 포함)
    ├── example_questions_seed.json  # 예시 질문
    ├── hr_data_seed.json            # 인사 데이터 (평가, 근태)
    └── org_seed.json                # 조직도 데이터
```

---

## 운영 가이드

### 인사규정 문서 추가/수정

1. `data/` 폴더에 마크다운 파일 추가 또는 수정
2. 재인덱싱 실행:
   ```bash
   # 로그인하여 JWT 토큰 획득
   TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

   # 재인덱싱
   curl -X POST http://localhost:8000/api/admin/reindex \
     -H "Authorization: Bearer $TOKEN"
   ```
   또는 관리자 페이지(`/admin/documents`)에서 "재인덱싱" 버튼 클릭

### 동의어 관리

검색 품질 개선을 위해 동의어를 관리할 수 있습니다.

- 관리자 페이지 `/admin/glossary`에서 용어의 **별칭(aliases)** 필드 수정
- 예: "시간외근무수당" 용어에 별칭 "야근수당, 초과근무수당, 잔업수당" 추가
- 코드 수정 없이 즉시 반영 (60초 캐시 후 자동 갱신)

### 데이터 초기화

모든 데이터를 삭제하고 처음부터 다시 시작하려면:

```bash
# 데이터 디렉토리 삭제
rm -rf D:/workplace/mkagent/case1data

# 백엔드 재시작 (자동으로 재인제스션 수행)
docker-compose restart
```

### 로그 확인

```bash
# 백엔드 로그 (실시간)
docker-compose logs -f backend

# 최근 100줄만
docker-compose logs --tail=100 backend
```

### 백엔드 중지/재시작

```bash
docker-compose stop      # 중지
docker-compose start     # 시작
docker-compose restart   # 재시작
docker-compose down      # 완전 종료 (컨테이너 삭제)
```

---

## 환경 변수

`docker-compose.yml`에서 설정 가능:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama 서버 주소 |
| `OLLAMA_MODEL` | `exaone3.5:7.8b` | LLM 모델 (답변 생성) |
| `OLLAMA_EMBED_MODEL` | `bge-m3` | 임베딩 모델 (벡터 변환) |
| `STORAGE_PATH` | `/app/storage` | 데이터 영속화 경로 |
| `DATA_PATH` | `/app/data` | 인사규정 MD 파일 경로 |
| `ADMIN_USER` | `admin` | 관리자 계정 |
| `ADMIN_PASS` | `admin` | 관리자 비밀번호 |

---

## 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| **LLM** | LGAI EXAONE 3.5 (via Ollama) | 7.8B |
| **임베딩** | BGE-M3 (via Ollama) | 1024차원 |
| **백엔드** | FastAPI + Uvicorn | Python 3.11 |
| **벡터 DB** | LanceDB | 0.17.0 |
| **관계형 DB** | DuckDB | 1.1.3 |
| **프론트엔드** | Next.js + React + Tailwind CSS | Next 15, React 19 |
| **컨테이너** | Docker | - |
| **인증** | JWT (python-jose) | HS256 |

---

## 알려진 한계

### 1. 대화 맥락 기억의 제한
- LLM에 전달하는 대화 히스토리는 **최근 3턴(6메시지)**으로 제한됩니다
- 오래 전 대화 내용을 참조하는 후속 질문에는 정확히 답변하지 못할 수 있습니다
- 예: 10턴 전에 논의한 "그 규정"을 다시 물으면 맥락을 잃을 수 있음

### 2. 구어체 한국어 검색의 한계
- 동의어 시스템으로 상당 부분 보완했지만, 등록되지 않은 신조어나 극단적 줄임말은 검색이 안될 수 있습니다
- 해결법: 관리자 페이지에서 동의어(aliases)를 추가하면 즉시 개선됩니다

### 3. LLM 환각(Hallucination)
- RAG로 실제 규정을 근거로 제공하지만, LLM이 규정에 없는 내용을 만들어낼 가능성이 있습니다
- 답변에 표시되는 **출처(Source) 카드**를 반드시 확인하세요
- temperature 0.4로 낮춰 환각을 줄이고 있지만 완전히 제거되지는 않습니다

### 4. 로컬 LLM 성능 제한
- `exaone3.5:7.8b`는 7.8B 파라미터 모델로, GPT-4 급 상용 모델 대비 추론 능력이 제한적입니다
- 복잡한 계산이나 여러 조항을 교차 분석하는 질문에 부정확할 수 있습니다
- GPU가 없으면 응답 시간이 수십 초 이상 소요될 수 있습니다

### 5. 동시 접속 제한
- DuckDB는 단일 프로세스만 쓰기 접근이 가능합니다
- 여러 사용자가 동시에 질문하면 DB 쓰기(대화 저장)에서 충돌이 발생할 수 있습니다
- 현재 단일 uvicorn 워커로 운영되며, 프로덕션 환경에서는 DB 계층 교체가 필요합니다

### 6. 인증 보안
- JWT 시크릿 키가 코드에 하드코딩되어 있습니다 (`hr-agent-secret-key-change-in-production`)
- 계정이 `admin/admin` 단일 계정입니다
- **프로덕션 배포 시 반드시 변경 필요**

### 7. 데이터 영속화
- LanceDB와 DuckDB 파일은 호스트 볼륨 마운트(`//d/workplace/mkagent`)에 저장됩니다
- Docker 볼륨이 아닌 호스트 경로에 의존하므로, 다른 환경에서는 `docker-compose.yml`의 볼륨 경로 수정이 필요합니다

---

## 라이선스

내부 프로젝트 (비공개)
