from __future__ import annotations
from datetime import datetime, timedelta
import sqlite3

from monitoring.anomaly_rules import detect_hourly_anomalies
from monitoring.live_store import DB_PATH, ensure_live_tables, read_live_logs
from monitoring.notifier import notify


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def _get_state(key: str) -> str | None:
    with _connect() as conn:
        row = conn.execute("SELECT value FROM monitor_state WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def _set_state(key: str, value: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO monitor_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def run_hourly_monitor(now: datetime | None = None, lookback_seconds: int = 3600) -> dict:
    ensure_live_tables()
    end_dt = now or datetime.now()
    end = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    start = _get_state("last_hourly_check") or (end_dt - timedelta(seconds=lookback_seconds)).strftime("%Y-%m-%d %H:%M:%S")
    df = read_live_logs(start=start, end=end)
    alerts = detect_hourly_anomalies(df)

    n = len(df)
    confirmed = df[df["user_confirmed_resolved"].isin([0, 1])] if n else df
    resolved = int((confirmed["user_confirmed_resolved"] == 1).sum()) if n else 0
    recontacts = int(df["recontact_within_24h"].sum()) if n else 0
    peer_reasks = int(df["peer_reask"].sum()) if n else 0
    input_tokens = int(df["input_tokens"].sum()) if n else 0
    output_tokens = int(df["output_tokens"].sum()) if n else 0
    api_calls = int(df["api_call_count"].sum()) if n else 0
    retries = int(df["retry_count"].sum()) if n else 0
    errors = int((~df["status_code"].fillna(0).astype(int).isin([0, 200])).sum()) if n else 0
    api_cost = float(df["api_cost_krw"].sum()) if n else 0.0
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO hourly_snapshots(
                window_start,window_end,requests,resolved,recontacts,peer_reasks,
                input_tokens,output_tokens,api_calls,retries,errors,api_cost_krw,anomaly_count,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (start,end,n,resolved,recontacts,peer_reasks,input_tokens,output_tokens,api_calls,retries,errors,api_cost,len(alerts),created_at),
        )

        if n:
            emp = df.copy()
            emp["total_tokens"] = emp["input_tokens"].fillna(0) + emp["output_tokens"].fillna(0)
            emp["is_error"] = ~emp["status_code"].fillna(0).astype(int).isin([0, 200])
            emp["is_resolved"] = emp["user_confirmed_resolved"].eq(1).astype(int)
            grouped = emp.groupby(["employee_id", "employee_department"], as_index=False).agg(
                requests=("request_id", "count"), resolved=("is_resolved", "sum"), api_calls=("api_call_count", "sum"),
                retries=("retry_count", "sum"), errors=("is_error", "sum"), input_tokens=("input_tokens", "sum"),
                output_tokens=("output_tokens", "sum"), total_tokens=("total_tokens", "sum"), api_cost_krw=("api_cost_krw", "sum")
            )
            conn.executemany(
                """
                INSERT INTO hourly_employee_snapshots(
                    window_start,window_end,employee_id,employee_department,requests,resolved,api_calls,retries,errors,
                    input_tokens,output_tokens,total_tokens,api_cost_krw,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                [(start,end,r.employee_id,r.employee_department,int(r.requests),int(r.resolved),int(r.api_calls),int(r.retries),int(r.errors),int(r.input_tokens),int(r.output_tokens),int(r.total_tokens),float(r.api_cost_krw),created_at) for r in grouped.itertuples(index=False)],
            )

        for alert in alerts:
            subject = f"[챗봇 모니터링][{alert['severity'].upper()}] {alert['alert_type']}"
            message = f"집계 구간: {start} ~ {end}\n{alert['message']}"
            sent_via, send_status = notify(subject, message)
            conn.execute(
                "INSERT INTO alert_history(created_at,window_start,window_end,severity,alert_type,employee_id,message,sent_via,send_status) VALUES (?,?,?,?,?,?,?,?,?)",
                (created_at,start,end,alert["severity"],alert["alert_type"],alert.get("employee_id"),alert["message"],sent_via,send_status),
            )

    _set_state("last_hourly_check", end)
    return {"window_start": start, "window_end": end, "requests": n, "alerts": len(alerts), "api_calls": api_calls, "retries": retries, "errors": errors}
