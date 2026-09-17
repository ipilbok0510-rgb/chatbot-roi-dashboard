import pandas as pd


def improvement_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """운영자가 확인할 개선 후보를 질문 topic 단위로 만든다."""
    if df.empty:
        return pd.DataFrame()
    work = df.copy()
    work["total_tokens"] = work["input_tokens"] + work["output_tokens"]
    g = work.groupby(["category", "topic"], as_index=False).agg(
        requests=("request_id", "count"),
        resolution_rate=("user_confirmed_resolved", "mean"),
        recontact_rate=("recontact_within_24h", "mean"),
        peer_reask_rate=("peer_reask", "mean"),
        avg_tokens=("total_tokens", "mean"),
        error_rate=("status_code", lambda s: (~s.eq(200)).mean()),
    )
    g["resolution_rate"] = (g["resolution_rate"] * 100).round(1)
    g["recontact_rate"] = (g["recontact_rate"] * 100).round(1)
    g["peer_reask_rate"] = (g["peer_reask_rate"] * 100).round(1)
    g["error_rate"] = (g["error_rate"] * 100).round(1)
    g["avg_tokens"] = g["avg_tokens"].round(0)

    def reason(row):
        reasons = []
        if row.resolution_rate < 35:
            reasons.append("낮은 해결률")
        if row.recontact_rate >= 35:
            reasons.append("재질문 높음")
        if row.peer_reask_rate >= 40:
            reasons.append("동료 재문의 높음")
        if row.avg_tokens >= 2200:
            reasons.append("Token 과다")
        if row.error_rate >= 5:
            reasons.append("API 오류")
        return ", ".join(reasons)

    g["개선후보"] = g.apply(reason, axis=1)
    return g[g["개선후보"] != ""].sort_values(["resolution_rate", "requests"], ascending=[True, False])
