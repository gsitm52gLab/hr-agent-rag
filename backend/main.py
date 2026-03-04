import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, chat, glossary, history, admin, org
from services.db import get_conn
from services.vector_store import get_db, TABLE_NAME


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시: 데이터가 없으면 자동 인제스션
    try:
        conn = get_conn()
        glossary_count = conn.execute("SELECT COUNT(*) FROM glossary").fetchone()[0]
        db = get_db()
        has_vectors = TABLE_NAME in db.table_names()

        if glossary_count == 0 or not has_vectors:
            print("[Startup] Data not found. Running auto-ingestion...")
            from services.ingestion import run_ingestion
            await run_ingestion()
        else:
            print(f"[Startup] Data OK: {glossary_count} glossary terms, vectors={'yes' if has_vectors else 'no'}")
    except Exception as e:
        print(f"[Startup] Auto-ingestion check failed: {e}")
    yield


app = FastAPI(title="HR Agent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(glossary.router)
app.include_router(history.router)
app.include_router(admin.router)
app.include_router(org.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
