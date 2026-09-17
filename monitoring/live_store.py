from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import sqlite3
import uuid
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "chatbot_efficiency.db"

LIVE_COLUMNS = [
    "request_id", "created_at", "employee_id", "employee_department",
    "category", "topic", "question_text", "question_type", "route",
    "answer_source", "knowledge_version", "api_required",
    "user_confirmed_resolved", "resolution_type", "recontact_within_24h",
    "peer_reask", "feedback_score", "response_seconds", "input_tokens",
    "output_tokens", "api_call_count", "retry_count", "status_code",
    "error_type", "api_cost_krw", "anomaly_flag",
]


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def ensure_live_tables() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS live_chatbot_logs (
                request_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                employee_department TEXT NOT NULL,
                category TEXT NOT NULL,
                topic TEXT NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                route TEXT NOT NULL,
                answer_source TEXT NOT NULL,
                knowledge_version TEXT,
                api_required INTEGER NOT NULL DEFAULT 0,
                user_confirmed_resolved INTEGER NOT NULL DEFAULT -1,
                resolution_type TEXT NOT NULL DEFAULT 'pending',
                recontact_within_24h INTEGER NOT NULL DEFAULT 0,
                peer_reask INTEGER NOT NULL DEFAULT 0,
                feedback_score REAL,
                response_seconds REAL NOT NULL DEFAULT 0,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                api_call_count INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                status_code INTEGER NOT NULL DEFAULT 0,
                error_type TEXT,
                api_cost_krw REAL NOT NULL DEFAULT 0,
                anomaly_flag INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_live_created_at ON live_chatbot_logs(created_at);
            CREATE INDEX IF NOT EXISTS idx_live_employee ON live_chatbot_logs(employee_id, created_at);

            CREATE TABLE IF NOT EXISTS hourly_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                requests INTEGER NOT NULL,
                resolved INTEGER NOT NULL,
                recontacts INTEGER NOT NULL,
                peer_reasks INTEGER NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                api_calls INTEGER NOT NULL,
                retries INTEGER NOT NULL,
                errors INTEGER NOT NULL,
                api_cost_krw REAL NOT NULL,
                anomaly_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hourly_employee_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                employee_department TEXT NOT NULL,
                requests INTEGER NOT NULL,
                resolved INTEGER NOT NULL,
                api_calls INTEGER NOT NULL,
                retries INTEGER NOT NULL,
                errors INTEGER NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                api_cost_krw REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                severity TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                employee_id TEXT,
                message TEXT NOT NULL,
                sent_via TEXT NOT NULL DEFAULT 'record_only',
                send_status TEXT NOT NULL DEFAULT 'not_sent'
            );

            CREATE TABLE IF NOT EXISTS monitor_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )


def new_request_id() -> str:
    return f"LIVE-{uuid.uuid4().hex[:16].upper()}"


def sanitize_question_text(text: str, max_length: int = 240) -> str:
    value = str(text or "").strip()
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", value)
    value = re.sub(r"\b\d{6,}\b", "[NUMBER]", value)
    return value[:max_length]


def log_chat_usage(**kwargs) -> str:
    ensure_live_tables()
    request_id = kwargs.get("request_id") or new_request_id()
    values = {
        "request_id": request_id,
        "created_at": kwargs.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "employee_id": kwargs.get("employee_id") or "DEMO-USER",
        "employee_department": kwargs.get("employee_department") or "미분류",
        "category": kwargs.get("category") or "미분류",
        "topic": kwargs.get("topic") or "미분류",
        "question_text": sanitize_question_text(kwargs.get("question_text", "")),
        "question_type": kwargs.get("question_type") or "text",
        "route": kwargs.get("route") or "UNKNOWN",
        "answer_source": kwargs.get("answer_source") or "UNKNOWN",
        "knowledge_version": kwargs.get("knowledge_version") or "",
        "api_required": int(kwargs.get("api_required", 0)),
        "user_confirmed_resolved": int(kwargs.get("user_confirmed_resolved", -1)),
        "resolution_type": kwargs.get("resolution_type") or "pending",
        "recontact_within_24h": int(kwargs.get("recontact_within_24h", 0)),
        "peer_reask": int(kwargs.get("peer_reask", 0)),
        "feedback_score": kwargs.get("feedback_score"),
        "response_seconds": float(kwargs.get("response_seconds", 0)),
        "input_tokens": int(kwargs.get("input_tokens", 0)),
        "output_tokens": int(kwargs.get("output_tokens", 0)),
        "api_call_count": int(kwargs.get("api_call_count", 0)),
        "retry_count": int(kwargs.get("retry_count", 0)),
        "status_code": int(kwargs.get("status_code", 0)),
        "error_type": kwargs.get("error_type"),
        "api_cost_krw": float(kwargs.get("api_cost_krw", 0)),
        "anomaly_flag": int(kwargs.get("anomaly_flag", 0)),
    }
    with _connect() as conn:
        cols = ",".join(LIVE_COLUMNS)
        marks = ",".join(["?"] * len(LIVE_COLUMNS))
        conn.execute(
            f"INSERT INTO live_chatbot_logs ({cols}) VALUES ({marks})",
            tuple(values[c] for c in LIVE_COLUMNS),
        )
    return request_id


def update_request_feedback(
    request_id: str,
    *,
    resolved: int,
    resolution_type: str,
    recontact_within_24h: int = 0,
    peer_reask: int = 0,
    feedback_score: float | None = None,
) -> None:
    ensure_live_tables()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE live_chatbot_logs
            SET user_confirmed_resolved=?, resolution_type=?,
                recontact_within_24h=?, peer_reask=?, feedback_score=?
            WHERE request_id=?
            """,
            (int(resolved), resolution_type, int(recontact_within_24h), int(peer_reask), feedback_score, request_id),
        )


def read_live_logs(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    ensure_live_tables()
    query = "SELECT * FROM live_chatbot_logs WHERE 1=1"
    params = []
    if start:
        query += " AND created_at > ?"
        params.append(start)
    if end:
        query += " AND created_at <= ?"
        params.append(end)
    query += " ORDER BY created_at"
    with _connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def read_hourly_snapshots(limit: int = 168) -> pd.DataFrame:
    ensure_live_tables()
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM hourly_snapshots ORDER BY id DESC LIMIT ?", conn, params=(limit,))


def read_employee_snapshots(window_end: str | None = None, limit: int = 500) -> pd.DataFrame:
    ensure_live_tables()
    with _connect() as conn:
        if window_end:
            return pd.read_sql_query(
                "SELECT * FROM hourly_employee_snapshots WHERE window_end=? ORDER BY total_tokens DESC LIMIT ?",
                conn, params=(window_end, limit),
            )
        return pd.read_sql_query("SELECT * FROM hourly_employee_snapshots ORDER BY id DESC LIMIT ?", conn, params=(limit,))


def read_alert_history(limit: int = 200) -> pd.DataFrame:
    ensure_live_tables()
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM alert_history ORDER BY id DESC LIMIT ?", conn, params=(limit,))


def latest_snapshot_end() -> str | None:
    ensure_live_tables()
    with _connect() as conn:
        row = conn.execute("SELECT window_end FROM hourly_snapshots ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else None


def pending_live_count() -> int:
    cutoff = latest_snapshot_end()
    with _connect() as conn:
        if cutoff:
            return int(conn.execute("SELECT COUNT(*) FROM live_chatbot_logs WHERE created_at > ?", (cutoff,)).fetchone()[0])
        return int(conn.execute("SELECT COUNT(*) FROM live_chatbot_logs").fetchone()[0])
