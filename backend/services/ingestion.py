"""
MD 파일 파싱 + 벡터 저장 파이프라인.
실행: python -m services.ingestion
"""
import asyncio
import glob
import json
import os
import re
import uuid

import config
from services.embedding import get_embeddings_batch
from services.vector_store import create_table
from services.db import get_conn


def parse_md_file(filepath: str) -> list[dict]:
    """Parse a markdown file into chunks by article (##)."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(filepath)
    # Extract document title from first # heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = title_match.group(1) if title_match else filename

    # Split by ## headings
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section or section.startswith("# ") and not section.startswith("## "):
            continue
        # Extract section title
        sec_match = re.match(r"^##\s+(.+)$", section, re.MULTILINE)
        sec_title = sec_match.group(1) if sec_match else ""
        chunks.append({
            "id": str(uuid.uuid4()),
            "document": doc_title,
            "filename": filename,
            "section": sec_title,
            "text": section,
        })
    return chunks


def load_all_md_files() -> list[dict]:
    """Load and parse all MD files from data directory."""
    md_pattern = os.path.join(config.DATA_PATH, "*.md")
    files = sorted(glob.glob(md_pattern))
    all_chunks = []
    for f in files:
        chunks = parse_md_file(f)
        all_chunks.extend(chunks)
        print(f"  Parsed {f}: {len(chunks)} chunks")
    return all_chunks


def load_glossary():
    """Load glossary seed data into DuckDB."""
    glossary_path = os.path.join(config.DATA_PATH, "glossary_seed.json")
    if not os.path.exists(glossary_path):
        print("  No glossary_seed.json found, skipping.")
        return

    with open(glossary_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    conn = get_conn()
    # Clear existing glossary
    conn.execute("DELETE FROM glossary")
    for item in items:
        conn.execute(
            "INSERT INTO glossary (id, term, definition, category, aliases) VALUES (nextval('glossary_id_seq'), ?, ?, ?, ?)",
            [item["term"], item["definition"], item.get("category", ""), item.get("aliases", "")],
        )
    print(f"  Loaded {len(items)} glossary terms.")


def load_example_questions():
    """Load example questions seed data into DuckDB."""
    eq_path = os.path.join(config.DATA_PATH, "example_questions_seed.json")
    if not os.path.exists(eq_path):
        print("  No example_questions_seed.json found, skipping.")
        return

    with open(eq_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    conn = get_conn()
    conn.execute("DELETE FROM example_questions")
    for item in items:
        conn.execute(
            "INSERT INTO example_questions (id, question, category, keywords) VALUES (nextval('example_questions_id_seq'), ?, ?, ?)",
            [item["question"], item.get("category", ""), item.get("keywords", "")],
        )
    print(f"  Loaded {len(items)} example questions.")


def load_org_chart():
    """Load organization chart seed data into DuckDB."""
    org_path = os.path.join(config.DATA_PATH, "org_seed.json")
    if not os.path.exists(org_path):
        print("  No org_seed.json found, skipping.")
        return

    with open(org_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_conn()
    conn.execute("DELETE FROM employees")
    conn.execute("DELETE FROM departments")

    for dept in data.get("departments", []):
        conn.execute(
            "INSERT INTO departments (id, name, description, parent_id, sort_order) VALUES (?, ?, ?, ?, ?)",
            [dept["id"], dept["name"], dept.get("description", ""), dept.get("parent_id"), dept.get("sort_order", 0)],
        )

    for emp in data.get("employees", []):
        conn.execute(
            "INSERT INTO employees (id, name, department_id, position, role, email, phone, is_department_head) VALUES (nextval('employees_id_seq'), ?, ?, ?, ?, ?, ?, ?)",
            [emp["name"], emp["department_id"], emp.get("position", ""), emp.get("role", ""), emp.get("email", ""), emp.get("phone", ""), emp.get("is_department_head", False)],
        )

    print(f"  Loaded {len(data.get('departments', []))} departments, {len(data.get('employees', []))} employees.")


def load_hr_data():
    """Load promotion history, evaluations, attendance, rewards/penalties into DuckDB."""
    hr_path = os.path.join(config.DATA_PATH, "hr_data_seed.json")
    if not os.path.exists(hr_path):
        print("  No hr_data_seed.json found, skipping.")
        return

    with open(hr_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_conn()

    # Clear existing data
    conn.execute("DELETE FROM rewards_penalties")
    conn.execute("DELETE FROM attendance_records")
    conn.execute("DELETE FROM employee_evaluations")
    conn.execute("DELETE FROM promotion_history")

    for row in data.get("promotion_history", []):
        conn.execute(
            "INSERT INTO promotion_history (id, year, position_from, position_to, eligible_count, promoted_count, avg_eval_score, min_eval_score) VALUES (nextval('promotion_history_id_seq'), ?, ?, ?, ?, ?, ?, ?)",
            [row["year"], row["position_from"], row["position_to"], row["eligible_count"], row["promoted_count"], row["avg_eval_score"], row["min_eval_score"]],
        )

    for row in data.get("employee_evaluations", []):
        conn.execute(
            "INSERT INTO employee_evaluations (id, employee_id, year, eval_score, performance_score, career_score, competency_score, training_score, reward_penalty_score, eval_grade) VALUES (nextval('employee_evaluations_id_seq'), ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [row["employee_id"], row["year"], row["eval_score"], row["performance_score"], row["career_score"], row["competency_score"], row["training_score"], row["reward_penalty_score"], row["eval_grade"]],
        )

    for row in data.get("attendance_records", []):
        conn.execute(
            "INSERT INTO attendance_records (id, employee_id, year, total_work_days, present_days, late_count, early_leave_count, absent_count, annual_leave_used, annual_leave_total, overtime_hours, attendance_rate) VALUES (nextval('attendance_records_id_seq'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [row["employee_id"], row["year"], row["total_work_days"], row["present_days"], row["late_count"], row["early_leave_count"], row["absent_count"], row["annual_leave_used"], row["annual_leave_total"], row["overtime_hours"], row["attendance_rate"]],
        )

    for row in data.get("rewards_penalties", []):
        conn.execute(
            "INSERT INTO rewards_penalties (id, employee_id, year, type, category, description, date) VALUES (nextval('rewards_penalties_id_seq'), ?, ?, ?, ?, ?, ?)",
            [row["employee_id"], row["year"], row["type"], row["category"], row["description"], row["date"]],
        )

    total = len(data.get("promotion_history", [])) + len(data.get("employee_evaluations", [])) + len(data.get("attendance_records", [])) + len(data.get("rewards_penalties", []))
    print(f"  Loaded HR data: {len(data.get('promotion_history', []))} promotion records, {len(data.get('employee_evaluations', []))} evaluations, {len(data.get('attendance_records', []))} attendance, {len(data.get('rewards_penalties', []))} rewards/penalties.")


def load_documents_to_db(chunks: list[dict]):
    """Store document info in DuckDB for admin management."""
    conn = get_conn()
    conn.execute("DELETE FROM documents")
    # Group chunks by filename to get unique documents
    docs = {}
    for c in chunks:
        fn = c["filename"]
        if fn not in docs:
            docs[fn] = {"filename": fn, "title": c["document"], "chunks": []}
        docs[fn]["chunks"].append(c["text"])

    for fn, doc in docs.items():
        doc_id = str(uuid.uuid4())
        full_content = "\n\n".join(doc["chunks"])
        conn.execute(
            "INSERT INTO documents (id, filename, title, content) VALUES (?, ?, ?, ?)",
            [doc_id, fn, doc["title"], full_content],
        )
    print(f"  Stored {len(docs)} documents in DuckDB.")


async def run_ingestion():
    print("=== HR Agent Data Ingestion ===")

    # 1. Parse MD files
    print("\n[1/4] Parsing MD files...")
    chunks = load_all_md_files()
    if not chunks:
        print("  No MD files found. Exiting.")
        return
    print(f"  Total chunks: {len(chunks)}")

    # 2. Generate embeddings
    print("\n[2/4] Generating embeddings via Ollama...")
    texts = [c["text"] for c in chunks]
    # Process in batches of 10
    all_embeddings = []
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = await get_embeddings_batch(batch)
        all_embeddings.extend(embeddings)
        print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} chunks")

    # 3. Store in LanceDB
    print("\n[3/4] Storing vectors in LanceDB...")
    vector_data = []
    for chunk, embedding in zip(chunks, all_embeddings):
        vector_data.append({
            "id": chunk["id"],
            "vector": embedding,
            "document": chunk["document"],
            "filename": chunk["filename"],
            "section": chunk["section"],
            "text": chunk["text"],
        })
    create_table(vector_data)
    print(f"  Stored {len(vector_data)} vectors.")

    # 4. Load glossary + example questions + org chart + HR data + document records
    print("\n[4/4] Loading glossary, example questions, org chart, HR data, and document records...")
    load_glossary()
    load_example_questions()
    load_org_chart()
    load_hr_data()
    load_documents_to_db(chunks)

    print("\n=== Ingestion Complete ===")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
