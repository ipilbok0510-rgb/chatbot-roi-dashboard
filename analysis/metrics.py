from __future__ import annotations
import math
import pandas as pd

PERIOD_LABELS = {
    "initial_1m": "초기 1개월",
    "month2": "2개월차",
    "month3": "3개월차",
}


def pct(num: float, den: float) -> float:
    return round((num / den * 100) if den else 0.0, 1)


def p95(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna().sort_values()
    if s.empty:
        return 0.0
    idx = max(0, math.ceil(len(s) * 0.95) - 1)
    return round(float(s.iloc[idx]), 2)


def baseline_metrics(df: pd.DataFrame) -> dict:
    support = df[df["source"] == "support_department"]
    return {
        "inquiries": int(len(df)),
        "avg_search_minutes": round(float(df["search_minutes"].mean()), 1),
        "avg_asking_minutes": round(float(df["asking_minutes"].mean()), 1),
        "avg_response_wait_minutes": round(float(df["response_wait_minutes"].mean()), 1),
        "avg_support_response_wait_minutes": round(float(support["response_wait_minutes"].mean()), 1) if not support.empty else 0.0,
        "avg_support_answering_minutes": round(float(support["answering_minutes"].mean()), 1) if not support.empty else 0.0,
        "resolved_rate": pct(df["resolved"].sum(), len(df)),
        "support_share": pct(len(support), len(df)),
    }


def request_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "requests": 0, "resolution_rate": 0, "recontact_rate": 0,
            "peer_reask_rate": 0, "faq_hit_rate": 0, "rag_route_rate": 0,
            "rag_resolution_rate": 0, "direct_llm_rate": 0, "llm_call_rate": 0,
            "token_per_request": 0, "token_per_resolved": 0,
            "avg_response_seconds": 0, "p95_response_seconds": 0,
            "retry_rate": 0, "api_error_rate": 0, "api_cost_per_request": 0,
            "avg_feedback_score": 0,
        }
    n = len(df)
    resolved = int(df["user_confirmed_resolved"].sum())
    rag = df[df["answer_source"] == "RAG"]
    api = df[df["api_call_count"] > 0]
    total_tokens = int((df["input_tokens"] + df["output_tokens"]).sum())
    return {
        "requests": n,
        "resolution_rate": pct(resolved, n),
        "recontact_rate": pct(df["recontact_within_24h"].sum(), n),
        "peer_reask_rate": pct(df["peer_reask"].sum(), n),
        "faq_hit_rate": pct((df["answer_source"] == "FAQ").sum(), n),
        "rag_route_rate": pct((df["answer_source"] == "RAG").sum(), n),
        "rag_resolution_rate": pct(rag["user_confirmed_resolved"].sum(), len(rag)),
        "direct_llm_rate": pct((df["answer_source"] == "LLM").sum(), n),
        "llm_call_rate": pct(len(api), n),
        "token_per_request": round(total_tokens / n, 0),
        "token_per_resolved": round(total_tokens / resolved, 0) if resolved else 0,
        "avg_response_seconds": round(float(df["response_seconds"].mean()), 2),
        "p95_response_seconds": p95(df["response_seconds"]),
        "retry_rate": pct((api["retry_count"] > 0).sum(), len(api)),
        "api_error_rate": pct((api["status_code"] != 200).sum(), len(api)),
        "api_cost_per_request": round(float(df["api_cost_krw"].sum()) / n, 2),
        "avg_feedback_score": round(float(df["feedback_score"].mean()), 2),
    }


def period_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for period in ["initial_1m", "month2", "month3"]:
        m = request_metrics(df[df["period"] == period])
        m["period"] = period
        m["기간"] = PERIOD_LABELS[period]
        rows.append(m)
    return pd.DataFrame(rows)


def topic_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    g = df.groupby(["category", "topic"], as_index=False).agg(
        요청=("request_id", "count"),
        해결률=("user_confirmed_resolved", "mean"),
        재질문율=("recontact_within_24h", "mean"),
        동료재문의율=("peer_reask", "mean"),
        평균응답초=("response_seconds", "mean"),
        평균피드백=("feedback_score", "mean"),
    )
    for col in ["해결률", "재질문율", "동료재문의율"]:
        g[col] = (g[col] * 100).round(1)
    g["평균응답초"] = g["평균응답초"].round(2)
    g["평균피드백"] = g["평균피드백"].round(2)
    return g.sort_values(["해결률", "요청"], ascending=[True, False])


def route_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    g = df.groupby("answer_source", as_index=False).agg(
        요청=("request_id", "count"),
        해결률=("user_confirmed_resolved", "mean"),
        입력토큰=("input_tokens", "sum"),
        출력토큰=("output_tokens", "sum"),
        API호출=("api_call_count", "sum"),
        API비용=("api_cost_krw", "sum"),
        평균응답초=("response_seconds", "mean"),
    )
    g["해결률"] = (g["해결률"] * 100).round(1)
    g["평균응답초"] = g["평균응답초"].round(2)
    g["API비용"] = g["API비용"].round(0)
    return g.sort_values("요청", ascending=False)
