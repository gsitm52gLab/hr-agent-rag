import os
import duckdb
import config

_conn = None


def get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(config.DUCKDB_PATH), exist_ok=True)
        _conn = duckdb.connect(config.DUCKDB_PATH)
        _init_schema(_conn)
    return _conn


def _init_schema(conn: duckdb.DuckDBPyConnection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id VARCHAR PRIMARY KEY,
            conversation_id VARCHAR,
            role VARCHAR,
            content TEXT,
            sources JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS glossary (
            id INTEGER PRIMARY KEY,
            term VARCHAR NOT NULL,
            definition TEXT NOT NULL,
            category VARCHAR,
            aliases VARCHAR DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS glossary_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY,
            query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS search_history_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_stats (
            id INTEGER PRIMARY KEY,
            query TEXT,
            response_time_ms INTEGER,
            source_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS search_stats_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR PRIMARY KEY,
            filename VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS example_questions (
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            category VARCHAR DEFAULT '',
            keywords VARCHAR DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS example_questions_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            description TEXT DEFAULT '',
            parent_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS departments_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            department_id INTEGER NOT NULL,
            position VARCHAR DEFAULT '',
            role VARCHAR DEFAULT '',
            email VARCHAR DEFAULT '',
            phone VARCHAR DEFAULT '',
            is_department_head BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS employees_id_seq START 1
    """)

    # --- Promotion / Attendance / Rewards tables ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS promotion_history (
            id INTEGER PRIMARY KEY,
            year INTEGER NOT NULL,
            position_from VARCHAR DEFAULT '',
            position_to VARCHAR DEFAULT '',
            eligible_count INTEGER DEFAULT 0,
            promoted_count INTEGER DEFAULT 0,
            avg_eval_score FLOAT DEFAULT 0,
            min_eval_score FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS promotion_history_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employee_evaluations (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            eval_score FLOAT DEFAULT 0,
            performance_score FLOAT DEFAULT 0,
            career_score FLOAT DEFAULT 0,
            competency_score FLOAT DEFAULT 0,
            training_score FLOAT DEFAULT 0,
            reward_penalty_score FLOAT DEFAULT 0,
            eval_grade VARCHAR DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS employee_evaluations_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            total_work_days INTEGER DEFAULT 0,
            present_days INTEGER DEFAULT 0,
            late_count INTEGER DEFAULT 0,
            early_leave_count INTEGER DEFAULT 0,
            absent_count INTEGER DEFAULT 0,
            annual_leave_used FLOAT DEFAULT 0,
            annual_leave_total FLOAT DEFAULT 0,
            overtime_hours FLOAT DEFAULT 0,
            attendance_rate FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS attendance_records_id_seq START 1
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rewards_penalties (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            type VARCHAR NOT NULL,
            category VARCHAR DEFAULT '',
            description TEXT DEFAULT '',
            date VARCHAR DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS rewards_penalties_id_seq START 1
    """)
