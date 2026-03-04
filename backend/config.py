import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")

STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/storage")
DATA_PATH = os.getenv("DATA_PATH", "/app/data")

LANCEDB_PATH = os.path.join(STORAGE_PATH, "case1data", "lancedb")
DUCKDB_PATH = os.path.join(STORAGE_PATH, "case1data", "duckdb", "hr_agent.duckdb")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")

JWT_SECRET = os.getenv("JWT_SECRET", "hr-agent-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

VECTOR_TOP_K = 5
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))  # bge-m3: 1024, nomic-embed-text: 768
CHUNK_SEPARATOR = "## "

# admin user ↔ employee mapping (admin = 박지훈 대리, employee_id=3)
ADMIN_EMPLOYEE_ID = int(os.getenv("ADMIN_EMPLOYEE_ID", "3"))
