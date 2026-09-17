from pathlib import Path
import pandas as pd

from analysis.metrics import baseline_metrics, request_metrics, period_summary

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def test_baseline_counts_and_wait_definition():
    df = pd.read_csv(DATA / "baseline_peer_inquiries.csv")
    m = baseline_metrics(df)
    assert m["inquiries"] == 250
    assert 35 <= m["avg_support_response_wait_minutes"] <= 50
    assert 7 <= m["avg_support_answering_minutes"] <= 12
    assert m["avg_support_response_wait_minutes"] > m["avg_support_answering_minutes"]


def test_period_resolution_targets():
    df = pd.read_csv(DATA / "chatbot_requests.csv")
    initial = request_metrics(df[df["period"] == "initial_1m"])
    month3 = request_metrics(df[df["period"] == "month3"])
    assert initial["requests"] == 600
    assert initial["resolution_rate"] == 30.0
    assert month3["requests"] == 850
    assert month3["resolution_rate"] == 45.1
    assert month3["recontact_rate"] < initial["recontact_rate"]
    assert month3["peer_reask_rate"] < initial["peer_reask_rate"]
    assert month3["faq_hit_rate"] > initial["faq_hit_rate"]
    assert month3["rag_route_rate"] > initial["rag_route_rate"]
    assert month3["llm_call_rate"] < initial["llm_call_rate"]


def test_period_summary_three_rows():
    df = pd.read_csv(DATA / "chatbot_requests.csv")
    out = period_summary(df)
    assert list(out["period"]) == ["initial_1m", "month2", "month3"]
