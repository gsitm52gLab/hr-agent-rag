from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from models.schemas import GlossaryItem, GlossaryCreate, GlossaryUpdate
from services.db import get_conn
from services.vector_store import invalidate_synonyms_cache

router = APIRouter(prefix="/api/glossary", tags=["glossary"])


@router.get("/search", response_model=list[GlossaryItem])
async def search_glossary(q: str = "", username: str = Depends(verify_token)):
    """Search glossary terms for autocomplete (matches term or aliases)."""
    conn = get_conn()
    if not q:
        return []
    rows = conn.execute(
        "SELECT id, term, definition, category, aliases, created_at FROM glossary WHERE term ILIKE ? OR aliases ILIKE ? ORDER BY term LIMIT 10",
        [f"%{q}%", f"%{q}%"],
    ).fetchall()
    return [
        GlossaryItem(id=r[0], term=r[1], definition=r[2], category=r[3], aliases=r[4] or "", created_at=r[5])
        for r in rows
    ]


@router.get("", response_model=list[GlossaryItem])
async def list_glossary(username: str = Depends(verify_token)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, term, definition, category, aliases, created_at FROM glossary ORDER BY term"
    ).fetchall()
    return [
        GlossaryItem(id=r[0], term=r[1], definition=r[2], category=r[3], aliases=r[4] or "", created_at=r[5])
        for r in rows
    ]


@router.post("", response_model=GlossaryItem)
async def create_glossary(item: GlossaryCreate, username: str = Depends(verify_token)):
    conn = get_conn()
    result = conn.execute(
        "INSERT INTO glossary (id, term, definition, category, aliases) VALUES (nextval('glossary_id_seq'), ?, ?, ?, ?) RETURNING id, term, definition, category, aliases, created_at",
        [item.term, item.definition, item.category, item.aliases or ""],
    ).fetchone()
    invalidate_synonyms_cache()
    return GlossaryItem(id=result[0], term=result[1], definition=result[2], category=result[3], aliases=result[4] or "", created_at=result[5])


@router.put("/{item_id}", response_model=GlossaryItem)
async def update_glossary(item_id: int, item: GlossaryUpdate, username: str = Depends(verify_token)):
    conn = get_conn()
    existing = conn.execute("SELECT id FROM glossary WHERE id = ?", [item_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Glossary item not found")

    updates = []
    params = []
    if item.term is not None:
        updates.append("term = ?")
        params.append(item.term)
    if item.definition is not None:
        updates.append("definition = ?")
        params.append(item.definition)
    if item.category is not None:
        updates.append("category = ?")
        params.append(item.category)
    if item.aliases is not None:
        updates.append("aliases = ?")
        params.append(item.aliases)

    if updates:
        params.append(item_id)
        conn.execute(f"UPDATE glossary SET {', '.join(updates)} WHERE id = ?", params)

    invalidate_synonyms_cache()
    row = conn.execute(
        "SELECT id, term, definition, category, aliases, created_at FROM glossary WHERE id = ?", [item_id]
    ).fetchone()
    return GlossaryItem(id=row[0], term=row[1], definition=row[2], category=row[3], aliases=row[4] or "", created_at=row[5])


@router.delete("/{item_id}")
async def delete_glossary(item_id: int, username: str = Depends(verify_token)):
    conn = get_conn()
    conn.execute("DELETE FROM glossary WHERE id = ?", [item_id])
    invalidate_synonyms_cache()
    return {"ok": True}
