import asyncio
import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from models.schemas import DocumentInfo, DocumentCreate, DocumentUpdate, SearchStats
from services.db import get_conn
from services.ingestion import run_ingestion
import config

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents(username: str = Depends(verify_token)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, title, content, created_at FROM documents ORDER BY filename"
    ).fetchall()
    return [
        DocumentInfo(id=r[0], filename=r[1], title=r[2], content=r[3], created_at=r[4])
        for r in rows
    ]


@router.post("/documents", response_model=DocumentInfo)
async def create_document(doc: DocumentCreate, username: str = Depends(verify_token)):
    # Save MD file to disk
    filepath = os.path.join(config.DATA_PATH, doc.filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(doc.content)

    # Save to DB
    doc_id = str(uuid.uuid4())
    conn = get_conn()
    conn.execute(
        "INSERT INTO documents (id, filename, title, content) VALUES (?, ?, ?, ?)",
        [doc_id, doc.filename, doc.title, doc.content],
    )
    row = conn.execute(
        "SELECT id, filename, title, content, created_at FROM documents WHERE id = ?", [doc_id]
    ).fetchone()
    return DocumentInfo(id=row[0], filename=row[1], title=row[2], content=row[3], created_at=row[4])


@router.put("/documents/{doc_id}", response_model=DocumentInfo)
async def update_document(doc_id: str, doc: DocumentUpdate, username: str = Depends(verify_token)):
    conn = get_conn()
    existing = conn.execute("SELECT id, filename FROM documents WHERE id = ?", [doc_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")

    updates = []
    params = []
    if doc.title is not None:
        updates.append("title = ?")
        params.append(doc.title)
    if doc.content is not None:
        updates.append("content = ?")
        params.append(doc.content)
        # Also update the file on disk
        filepath = os.path.join(config.DATA_PATH, existing[1])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(doc.content)

    if updates:
        params.append(doc_id)
        conn.execute(f"UPDATE documents SET {', '.join(updates)} WHERE id = ?", params)

    row = conn.execute(
        "SELECT id, filename, title, content, created_at FROM documents WHERE id = ?", [doc_id]
    ).fetchone()
    return DocumentInfo(id=row[0], filename=row[1], title=row[2], content=row[3], created_at=row[4])


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, username: str = Depends(verify_token)):
    conn = get_conn()
    existing = conn.execute("SELECT filename FROM documents WHERE id = ?", [doc_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove file from disk
    filepath = os.path.join(config.DATA_PATH, existing[0])
    if os.path.exists(filepath):
        os.remove(filepath)

    conn.execute("DELETE FROM documents WHERE id = ?", [doc_id])
    return {"ok": True}


@router.post("/reindex")
async def reindex(username: str = Depends(verify_token)):
    """Re-run the ingestion pipeline to rebuild vector index."""
    await run_ingestion()
    return {"ok": True, "message": "Reindexing complete"}


@router.get("/stats", response_model=SearchStats)
async def get_stats(username: str = Depends(verify_token)):
    conn = get_conn()

    total = conn.execute("SELECT COUNT(*) FROM search_stats").fetchone()[0]
    avg_time = conn.execute("SELECT COALESCE(AVG(response_time_ms), 0) FROM search_stats").fetchone()[0]

    top_queries = conn.execute(
        "SELECT query, COUNT(*) as cnt FROM search_stats GROUP BY query ORDER BY cnt DESC LIMIT 10"
    ).fetchall()

    daily = conn.execute(
        "SELECT CAST(created_at AS DATE) as day, COUNT(*) as cnt FROM search_stats GROUP BY day ORDER BY day DESC LIMIT 30"
    ).fetchall()

    return SearchStats(
        total_queries=total,
        avg_response_time_ms=round(avg_time, 1),
        top_queries=[{"query": q[0], "count": q[1]} for q in top_queries],
        daily_stats=[{"date": str(d[0]), "count": d[1]} for d in daily],
    )
