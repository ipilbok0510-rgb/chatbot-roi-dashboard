from pathlib import Path
import sys
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"
DB = ROOT / "database" / "chatbot_efficiency.db"
DB.parent.mkdir(parents=True, exist_ok=True)

TABLES = {
    "baseline_peer_inquiries": "baseline_peer_inquiries.csv",
    "baseline_summary": "baseline_summary.csv",
    "chatbot_requests": "chatbot_requests.csv",
    "kpi_period_summary": "kpi_period_summary.csv",
    "company_profile": "company_profile.csv",
    "faq": "faq.csv",
    "system_metrics": "system_metrics.csv",
    "improvement_actions": "improvement_actions.csv",
    "benchmark_sources": "benchmark_sources.csv",
}

with sqlite3.connect(DB) as conn:
    for table, filename in TABLES.items():
        path = DATA / filename
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"{table}: {len(df):,} rows")

# 실시간 로그/집계 테이블은 monitoring 모듈에서 생성한다.
from monitoring.live_store import ensure_live_tables
ensure_live_tables()
print(f"DB created: {DB}")
