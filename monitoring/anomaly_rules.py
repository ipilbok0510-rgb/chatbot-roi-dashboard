from __future__ import annotations
import pandas as pd


def detect_hourly_anomalies(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    work = df.copy()
    work["total_tokens"] = work["input_tokens"].fillna(0) + work["output_tokens"].fillna(0)
    alerts: list[dict] = []

    api = work[work["api_call_count"].fillna(0) > 0]
    errors = api[~api["status_code"].fillna(0).astype(int).isin([0, 200])]
    if not errors.empty:
        counts = errors["error_type"].fillna("unknown").value_counts().to_dict()
        alerts.append({
            "severity": "high" if len(errors) >= 3 else "medium",
            "alert_type": "api_error",
            "employee_id": None,
            "message": f"API 최종 오류 {len(errors)}건 발생: {counts}. 429/Timeout/5xx와 외부 API 상태를 확인하세요.",
        })

    if len(api) >= 10:
        rate = len(errors) / len(api)
        if rate >= 0.08:
            alerts.append({
                "severity": "high",
                "alert_type": "api_error_rate",
                "employee_id": None,
                "message": f"최근 API 오류율이 {rate*100:.1f}%입니다. Rate Limit, Timeout, Retry 정책을 확인하세요.",
            })

    retry_total = int(work["retry_count"].fillna(0).sum())
    if retry_total >= 5:
        alerts.append({
            "severity": "medium",
            "alert_type": "retry_spike",
            "employee_id": None,
            "message": f"최근 구간 API 재시도 {retry_total}회 발생. 429/Timeout/5xx와 최대 재시도 횟수를 확인하세요.",
        })

    heavy = work[work["total_tokens"] >= 6000]
    if not heavy.empty:
        alerts.append({
            "severity": "medium",
            "alert_type": "high_token_request",
            "employee_id": None,
            "message": f"요청당 6,000 Token 이상 {len(heavy)}건. RAG Top-K, Context 길이, 답변 길이를 확인하세요.",
        })

    token_rows = work[work["total_tokens"] > 0]
    if not token_rows.empty:
        per_emp = token_rows.groupby(["employee_department", "employee_id"], as_index=False).agg(
            requests=("request_id", "count"), total_tokens=("total_tokens", "sum"), retries=("retry_count", "sum")
        )
        avg = per_emp.groupby("employee_department")["total_tokens"].mean().rename("dept_avg")
        per_emp = per_emp.join(avg, on="employee_department")
        suspicious = per_emp[(per_emp["requests"] >= 3) & (per_emp["total_tokens"] >= 15000) & (per_emp["total_tokens"] >= per_emp["dept_avg"] * 3)]
        for row in suspicious.itertuples(index=False):
            alerts.append({
                "severity": "medium",
                "alert_type": "employee_token_outlier",
                "employee_id": row.employee_id,
                "message": (
                    f"직원 {row.employee_id} Token {int(row.total_tokens):,}이 소속부서 평균 {row.dept_avg:.0f}의 3배 이상입니다. "
                    "개인 문제로 단정하지 말고 질문 수, RAG Context, Retry, 오류를 함께 확인하세요."
                ),
            })

    feedback = work[work["user_confirmed_resolved"].isin([0, 1])]
    if len(feedback) >= 10:
        rate = feedback["user_confirmed_resolved"].mean()
        if rate < 0.30:
            alerts.append({
                "severity": "medium",
                "alert_type": "low_resolution_rate",
                "employee_id": None,
                "message": f"최근 사용자 확인 해결률이 {rate*100:.1f}%입니다. FAQ/RAG 지식 품질과 반복 미해결 topic을 확인하세요.",
            })

    return alerts
