from fastapi import APIRouter, Depends

from auth import verify_token
from models.schemas import RecentSearch, ExampleQuestion
from services.db import get_conn

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/recent", response_model=list[RecentSearch])
async def recent_searches(q: str = "", username: str = Depends(verify_token)):
    """Get recent search queries for autocomplete."""
    conn = get_conn()
    if q:
        rows = conn.execute(
            "SELECT id, query, created_at FROM search_history WHERE query ILIKE ? ORDER BY created_at DESC LIMIT 5",
            [f"%{q}%"],
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, query, created_at FROM search_history ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
    return [RecentSearch(id=r[0], query=r[1], created_at=r[2]) for r in rows]


@router.get("/examples", response_model=list[ExampleQuestion])
async def example_questions(q: str = "", username: str = Depends(verify_token)):
    """Get example questions matching user input keywords."""
    conn = get_conn()
    if not q or len(q) < 1:
        return []
    rows = conn.execute(
        "SELECT id, question, category, keywords FROM example_questions WHERE question ILIKE ? OR keywords ILIKE ? ORDER BY id LIMIT 5",
        [f"%{q}%", f"%{q}%"],
    ).fetchall()
    return [ExampleQuestion(id=r[0], question=r[1], category=r[2], keywords=r[3]) for r in rows]
