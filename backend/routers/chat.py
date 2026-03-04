import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from auth import verify_token
from models.schemas import ChatRequest, Conversation, ConversationDetail, ChatMessage
from services.rag import rag_query
from services.db import get_conn

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(req: ChatRequest, username: str = Depends(verify_token)):
    """RAG chat endpoint with streaming response."""
    conversation_id = req.conversation_id or str(uuid.uuid4())
    conn = get_conn()

    # Create conversation if new
    existing = conn.execute(
        "SELECT id FROM conversations WHERE id = ?", [conversation_id]
    ).fetchone()
    if not existing:
        title = req.message[:50] + ("..." if len(req.message) > 50 else "")
        conn.execute(
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            [conversation_id, title],
        )

    # Save user message
    user_msg_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'user', ?)",
        [user_msg_id, conversation_id, req.message],
    )

    async def stream():
        full_response = ""
        sources_data = None

        async for chunk in rag_query(req.message, conversation_id):
            data = json.loads(chunk.strip())
            if data["type"] == "token":
                full_response += data["content"]
            elif data["type"] == "sources":
                sources_data = data["sources"]
            yield chunk

        # Save assistant message
        asst_msg_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, sources) VALUES (?, ?, 'assistant', ?, ?)",
            [asst_msg_id, conversation_id, full_response, json.dumps(sources_data)],
        )
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            [conversation_id],
        )

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/history", response_model=list[Conversation])
async def list_conversations(username: str = Depends(verify_token)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    return [
        Conversation(id=r[0], title=r[1], created_at=r[2], updated_at=r[3])
        for r in rows
    ]


@router.get("/history/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, username: str = Depends(verify_token)):
    conn = get_conn()
    conv = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
        [conversation_id],
    ).fetchone()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs = conn.execute(
        "SELECT id, conversation_id, role, content, sources, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at",
        [conversation_id],
    ).fetchall()

    return ConversationDetail(
        conversation=Conversation(id=conv[0], title=conv[1], created_at=conv[2], updated_at=conv[3]),
        messages=[
            ChatMessage(
                id=m[0],
                conversation_id=m[1],
                role=m[2],
                content=m[3],
                sources=json.loads(m[4]) if m[4] else None,
                created_at=m[5],
            )
            for m in msgs
        ],
    )


@router.delete("/history/{conversation_id}")
async def delete_conversation(conversation_id: str, username: str = Depends(verify_token)):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", [conversation_id])
    conn.execute("DELETE FROM conversations WHERE id = ?", [conversation_id])
    return {"ok": True}
