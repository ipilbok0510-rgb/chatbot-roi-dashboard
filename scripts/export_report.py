from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.db import read_table
from analysis.metrics import period_summary, topic_summary, route_summary
from analysis.anomaly import improvement_candidates

OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

requests = read_table("chatbot_requests")
period_summary(requests).to_csv(OUT / "period_summary.csv", index=False, encoding="utf-8-sig")
topic_summary(requests).to_csv(OUT / "topic_summary.csv", index=False, encoding="utf-8-sig")
route_summary(requests).to_csv(OUT / "route_summary.csv", index=False, encoding="utf-8-sig")
improvement_candidates(requests).to_csv(OUT / "improvement_candidates.csv", index=False, encoding="utf-8-sig")
print(f"Exported reports to {OUT}")
