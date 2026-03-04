"""Test hybrid search with colloquial Korean queries."""
import asyncio
from services.vector_store import keyword_search, search
from services.embedding import get_embedding

queries = [
    ("연차 며칠이야?", "휴가"),
    ("월급날 언제야?", "급여"),
    ("야근하면 돈 더줘?", "근무"),
    ("해고되면 어떻게돼?", "퇴직"),
    ("승진하려면 뭐해야돼?", "승진"),
    ("병가 쓸수있어?", "휴가"),
    ("출산하면 휴가줘?", "휴가"),
    ("징계받으면 어떻게되?", "징계"),
    ("옷 뭐입어야해?", "복장"),
    ("인턴도 보험들어줘?", "복리후생"),
    ("경조사비 얼마야?", "복리후생"),
    ("수습기간 얼마야?", "채용"),
    ("육아휴직 쓸수있어?", "휴가"),
    ("연봉 어떻게 정해져?", "급여"),
    ("정년 몇살이야?", "퇴직"),
    ("회사에서 운동화 신어도돼?", "복장"),
    ("퇴직금 어떻게 계산해?", "퇴직"),
    ("야근수당 얼마줘?", "급여"),
    ("금요일에 청바지 입어도되?", "복장"),
    ("임신하면 쉴수있어?", "휴가"),
]


async def main():
    print("=" * 100)
    print(f"  {'Query':<28} | {'Want':<8} | {'Keyword Result':<30} | {'Vector Result':<30} | Status")
    print("=" * 100)

    ok = 0
    fail = 0
    for q, expected in queries:
        kw = keyword_search(q, top_k=1)
        kw_doc = kw[0]["document"] if kw else "(none)"

        vec = await get_embedding(q)
        vr = search(vec, top_k=1)
        vr_doc = vr[0]["document"] if vr else "(none)"

        kw_ok = expected in kw_doc
        vr_ok = expected in vr_doc
        hybrid_ok = kw_ok or vr_ok

        if hybrid_ok:
            status = "OK"
            ok += 1
        else:
            status = "FAIL"
            fail += 1

        print(f"  {q:<28} | {expected:<8} | {kw_doc[:28]:<30} | {vr_doc[:28]:<30} | {status}")

    print("=" * 100)
    print(f"  Results: {ok} OK, {fail} FAIL out of {len(queries)}")


asyncio.run(main())
