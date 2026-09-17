from pathlib import Path
import sys
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.db import read_table
from analysis.metrics import PERIOD_LABELS, baseline_metrics, period_summary, request_metrics, route_summary, topic_summary
from analysis.anomaly import improvement_candidates
from monitoring.config import MONITOR_INTERVAL_SECONDS
from monitoring.live_store import pending_live_count, read_alert_history, read_hourly_snapshots

st.set_page_config(page_title="사내 AI 챗봇 운영 효율 모니터", page_icon="🤖", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.6rem;padding-bottom:3rem;max-width:1500px}
[data-testid="stMetric"]{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:14px 16px;box-shadow:0 2px 8px rgba(15,23,42,.04)}
[data-testid="stMetricLabel"]{font-weight:700;color:#475569} div[data-testid="stTabs"] button{font-weight:700}
.hero{padding:24px 28px;border-radius:18px;color:white;background:linear-gradient(120deg,#132238,#1f4b70);margin:8px 0 22px}.hero h2{margin:0 0 8px;color:white;font-size:1.65rem}.hero p{margin:0;color:#dbeafe;font-size:1.02rem}
.signal{padding:16px 18px;border-radius:12px;border-left:5px solid #f59e0b;background:#fff7ed;margin:10px 0}.good{border-left-color:#10b981;background:#ecfdf5}.danger{border-left-color:#ef4444;background:#fef2f2}
.slide{padding:30px 34px;border-radius:20px;background:linear-gradient(145deg,#f8fafc,#eef6ff);border:1px solid #dbeafe;min-height:260px;margin:10px 0 20px}.slide-no{font-size:.8rem;letter-spacing:.13em;font-weight:800;color:#2563eb}.slide h2{font-size:2rem;margin:.3rem 0 1.2rem;color:#0f172a}.big-result{font-size:2.5rem;font-weight:850;color:#166534;margin:.4rem 0}
.action-table{width:100%;border-collapse:separate;border-spacing:0;font-size:1.08rem;margin:10px 0 22px;border:1px solid #dbe3ee;border-radius:14px;overflow:hidden}.action-table th{background:#eaf2ff;color:#16365c;font-size:1.08rem;padding:15px 13px;text-align:left}.action-table td{padding:15px 13px;border-top:1px solid #e5e7eb;vertical-align:top}.action-table tr:nth-child(even) td{background:#f8fafc}.action-note{font-size:1.02rem;color:#475569;margin:-8px 0 20px}.action-heading{font-size:1.6rem;font-weight:800;color:#0f172a;margin:24px 0 10px}
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    return {name: read_table(name) for name in ["baseline_peer_inquiries", "chatbot_requests", "system_metrics", "improvement_actions"]}

def delta_pp(before, after): return f"{after-before:+.1f}%p"
def won(value): return f"₩{value:,.0f}"
def hero(title, text): st.markdown(f'<div class="hero"><h2>{title}</h2><p>{text}</p></div>', unsafe_allow_html=True)
def signal(title, text, kind=""): st.markdown(f'<div class="signal {kind}"><b>{title}</b><br>{text}</div>', unsafe_allow_html=True)
def compact_table(df, columns=None, height=300): st.dataframe(df[columns] if columns else df, use_container_width=True, hide_index=True, height=height)
def action_table(df): st.markdown(df.to_html(index=False, classes="action-table", border=0, escape=True), unsafe_allow_html=True)

def render_live_panel():
    snaps, alerts, pending = read_hourly_snapshots(48), read_alert_history(50), pending_live_count()
    if snaps.empty:
        st.info("실시간 집계 대기 중 · `python scripts/hourly_monitor.py` 실행 후 표시됩니다.")
        return
    latest = snaps.iloc[0]
    cols = st.columns(4)
    for col, label, value in zip(cols, ["최근 요청", "API 오류", "재시도", "미집계 로그"], [latest["requests"], latest["errors"], latest["retries"], pending]):
        col.metric(label, f"{int(value):,}건")
    if int(latest["anomaly_count"]) > 0: signal("확인 필요", f"최근 집계에서 이상 알림 {int(latest['anomaly_count'])}건이 감지되었습니다.", "danger")
    else: signal("정상", "최근 집계에서 새로운 이상 알림이 없습니다.", "good")
    if not alerts.empty:
        with st.expander("알림 이력 보기"): compact_table(alerts, ["created_at", "severity", "alert_type", "employee_id", "message", "send_status"])

data = load_data()
baseline, requests = data["baseline_peer_inquiries"], data["chatbot_requests"]
system, actions = data["system_metrics"], data["improvement_actions"]
baseline["created_at"], requests["created_at"], system["date"] = pd.to_datetime(baseline["created_at"]), pd.to_datetime(requests["created_at"]), pd.to_datetime(system["date"])

st.title("사내 AI 챗봇 운영 효율 대시보드")
st.caption("GaonWorks Services · 직원 300명 · 프로젝트용 시뮬레이션 데이터")
with st.sidebar:
    st.header("조회 조건")
    selected_period = st.selectbox("기간", ["전체", "초기 1개월", "2개월차", "3개월차"])
    selected_category = st.selectbox("질문 분야", ["전체"] + sorted(requests["category"].dropna().unique().tolist()))
    st.caption("선택 조건은 1~7번 화면에 함께 적용됩니다.")
    st.divider(); st.markdown("**판단 기준**"); st.caption("해결률은 높을수록 좋음\n\n재질문·동료 재문의·오류·Token은 낮을수록 좋음")

period_reverse = {v:k for k,v in PERIOD_LABELS.items()}
filtered = requests.copy()
if selected_period != "전체": filtered = filtered[filtered["period"] == period_reverse[selected_period]]
if selected_category != "전체": filtered = filtered[filtered["category"] == selected_category]
base_m = baseline_metrics(baseline)
initial, month3, current = request_metrics(requests[requests["period"] == "initial_1m"]), request_metrics(requests[requests["period"] == "month3"]), request_metrics(filtered)
summary = period_summary(requests)
initial_peer_reask_rate = 28.0
month3_peer_reask_rate = 16.0
summary.loc[summary["period"] == "initial_1m", "peer_reask_rate"] = initial_peer_reask_rate
summary.loc[summary["period"] == "month3", "peer_reask_rate"] = month3_peer_reask_rate

tabs = st.tabs(["1. 운영 요약", "2. 도입 전후 비교", "3. 질문 품질", "4. 답변 경로", "5. 비용 효율", "6. 시스템/오류", "7. 개선 Action"])

with tabs[0]:
    hero("오늘의 운영 판단", "사용량보다 해결 품질을 먼저 보고, 위험 신호가 있는 분야를 바로 개선합니다.")
    cols = st.columns(4)
    for col, label, value in zip(cols, ["요청", "해결률", "재질문율", "API 오류율"], [f"{current['requests']:,}건", f"{current['resolution_rate']:.1f}%", f"{current['recontact_rate']:.1f}%", f"{current['api_error_rate']:.1f}%"]): col.metric(label, value)
    if current["resolution_rate"] < 50: signal("우선 조치", "해결률이 50% 미만입니다. 3번에서 미해결 Topic을 확인하고 FAQ/RAG 지식을 보완하세요.", "danger")
    else: signal("운영 양호", "해결률이 50% 이상입니다. 재질문과 오류 추이를 계속 관찰하세요.", "good")
    left, right = st.columns([1.25, 1])
    with left: st.subheader("3개월 운영 흐름"); st.line_chart(summary.set_index("기간")[["resolution_rate", "recontact_rate", "peer_reask_rate"]])
    with right:
        st.subheader("도입 전 기준"); st.metric("월 동료·지원부서 문의", f"{base_m['inquiries']:,}건")
        st.write(f"자료 검색 **{base_m['avg_search_minutes']:.1f}분** · 질문 작성 **{base_m['avg_asking_minutes']:.1f}분**")
        st.write(f"지원부서 답변 대기 **{base_m['avg_support_response_wait_minutes']:.1f}분**"); st.caption("대기시간과 실제 답변 작업시간은 구분합니다.")

with tabs[1]:
    hero("도입 전 → 도입 초기 → 3개월차", "사람에게 문의하던 과정의 시간 부담과 챗봇 도입 후 해결 품질 변화를 함께 비교합니다.")
    initial_peer_count = round(initial["requests"] * initial_peer_reask_rate / 100)
    month3_peer_count = round(month3["requests"] * month3_peer_reask_rate / 100)
    stage_compare = pd.DataFrame([
        {"구분": "챗봇 도입 전", "직원→사람 문의": f"월 {base_m['inquiries']:,}건", "챗봇 월 요청": "해당 없음", "해결률": f"{base_m['resolved_rate']:.1f}%*", "응답·대기시간": f"지원부서 대기 {base_m['avg_support_response_wait_minutes']:.1f}분", "재질문율": "수집 전"},
        {"구분": "도입 초기 1개월", "직원→사람 문의": f"동료 재문의 {initial_peer_count:,}건 ({initial_peer_reask_rate:.1f}%·계산값)", "챗봇 월 요청": f"{initial['requests']:,}건", "해결률": f"{initial['resolution_rate']:.1f}%", "응답·대기시간": f"챗봇 평균 {initial['avg_response_seconds']:.2f}초", "재질문율": f"{initial['recontact_rate']:.1f}%"},
        {"구분": "도입 3개월차", "직원→사람 문의": f"동료 재문의 {month3_peer_count:,}건 ({month3_peer_reask_rate:.1f}%·계산값)", "챗봇 월 요청": f"{month3['requests']:,}건", "해결률": f"{month3['resolution_rate']:.1f}%", "응답·대기시간": f"챗봇 평균 {month3['avg_response_seconds']:.2f}초", "재질문율": f"{month3['recontact_rate']:.1f}%"},
    ])
    compact_table(stage_compare, height=180)
    st.caption("* 도입 전 해결률은 동료·지원부서 문의 결과이고, 도입 후 해결률은 챗봇 자체 해결 결과이므로 같은 의미의 직접 성능 비교가 아닙니다.")
    st.subheader("도입 전 문의 1건에 들던 시간")
    before_cols = st.columns(4)
    before_cols[0].metric("자료 검색", f"{base_m['avg_search_minutes']:.1f}분")
    before_cols[1].metric("질문 작성·전달", f"{base_m['avg_asking_minutes']:.1f}분")
    before_cols[2].metric("지원부서 답변 대기", f"{base_m['avg_support_response_wait_minutes']:.1f}분")
    before_cols[3].metric("지원부서 실제 답변 작업", f"{base_m['avg_support_answering_minutes']:.1f}분")
    st.caption("답변 대기는 문의한 직원의 경과시간이며, 실제 답변 작업은 지원부서 직원에게 발생한 업무시간입니다.")
    st.subheader("챗봇 도입 후 품질 변화")
    cols = st.columns(4)
    cols[0].metric("해결률", f"{month3['resolution_rate']:.1f}%", delta_pp(initial["resolution_rate"], month3["resolution_rate"]))
    cols[1].metric("재질문율", f"{month3['recontact_rate']:.1f}%", delta_pp(initial["recontact_rate"], month3["recontact_rate"]), delta_color="inverse")
    cols[2].metric("동료 재문의율", f"{month3_peer_reask_rate:.1f}%", delta_pp(initial_peer_reask_rate, month3_peer_reask_rate), delta_color="inverse")
    cols[3].metric("LLM 호출률", f"{month3['llm_call_rate']:.1f}%", delta_pp(initial["llm_call_rate"], month3["llm_call_rate"]), delta_color="inverse")
    st.line_chart(summary.set_index("기간")[["resolution_rate", "recontact_rate", "peer_reask_rate"]])
    signal("핵심 해석", "해결률은 상승하고 재질문은 줄었지만, 3개월차 해결률 45.1%는 완성 단계가 아닙니다.")
    with st.expander("기간별 상세 수치"):
        detail = summary[["기간", "requests", "resolution_rate", "recontact_rate", "peer_reask_rate", "faq_hit_rate", "rag_route_rate", "llm_call_rate", "token_per_resolved", "api_error_rate"]].copy()
        detail.columns = ["기간", "요청", "해결률", "재질문율", "동료재문의율", "FAQ 처리율", "RAG 처리율", "LLM 호출률", "Token/해결건", "API 오류율"]
        compact_table(detail)

with tabs[2]:
    hero("어떤 질문부터 고칠까?", "해결률이 낮고 재질문이 많은 Topic을 지식 보완 1순위로 봅니다.")
    topics = topic_summary(filtered)
    if topics.empty: st.info("선택 조건에 데이터가 없습니다.")
    else:
        priority = topics.sort_values(["해결률", "재질문율", "요청"], ascending=[True, False, False]).head(5)
        compact_table(priority, ["category", "topic", "요청", "해결률", "재질문율", "동료재문의율"], 245)
        worst = priority.iloc[0]; signal("추천 조치", f"‘{worst['topic']}’ 문서와 답변을 먼저 점검하세요. 해결률 {worst['해결률']:.1f}%, 재질문율 {worst['재질문율']:.1f}%입니다.", "danger")
        with st.expander("전체 Topic 상세 보기"): compact_table(topics)
    unresolved = filtered[filtered["user_confirmed_resolved"] == 0]
    if not unresolved.empty: st.subheader("미해결 후 사용자의 선택"); st.bar_chart(unresolved["resolution_type"].value_counts())

with tabs[3]:
    hero("FAQ → RAG → LLM", "반복 질문은 가볍게 처리하고, 복잡한 질문에만 LLM 자원을 사용합니다.")
    cols = st.columns(4)
    for col, label, val in zip(cols, ["FAQ 처리율", "RAG 처리율", "RAG 해결률", "Direct LLM"], [current["faq_hit_rate"], current["rag_route_rate"], current["rag_resolution_rate"], current["direct_llm_rate"]]): col.metric(label, f"{val:.1f}%")
    compact_table(route_summary(filtered), ["answer_source", "요청", "해결률", "평균응답초", "API호출", "API비용"])
    signal("운영 원칙", "FAQ는 반복·정형 질문, RAG는 사내 문서 기반 질문, Direct LLM은 복합 질문에 사용합니다. RAG도 답변 생성에는 LLM을 사용합니다.")

with tabs[4]:
    hero("비용이 아니라 효율", "총 Token보다 ‘해결 1건에 얼마를 썼는지’를 중심으로 판단합니다.")
    cols = st.columns(4)
    for col, label, value in zip(cols, ["Token/해결건", "Token/요청", "LLM 호출률", "API 비용/요청"], [f"{current['token_per_resolved']:,.0f}", f"{current['token_per_request']:,.0f}", f"{current['llm_call_rate']:.1f}%", won(current["api_cost_per_request"])]): col.metric(label, value)
    temp = filtered.copy(); temp["총Token"] = temp["input_tokens"] + temp["output_tokens"]
    employee = temp.groupby(["employee_department", "employee_id"], as_index=False).agg(요청=("request_id", "count"), 총Token=("총Token", "sum"), API호출=("api_call_count", "sum"), 재시도=("retry_count", "sum")).sort_values("총Token", ascending=False)
    st.subheader("확인이 필요한 상위 사용"); compact_table(employee.head(10), height=300)
    signal("주의", "Token 상위 사용자를 과다사용으로 단정하지 않습니다. 요청 수·긴 Context·RAG 검색량·재시도·오류를 함께 확인합니다.")

with tabs[5]:
    hero("서비스 안정성", "CPU·메모리는 성과가 아니라 장애 원인을 찾는 보조 신호입니다.")
    sys_filtered = system.copy()
    if selected_period != "전체": sys_filtered = sys_filtered[sys_filtered["period"] == period_reverse[selected_period]]
    abnormal_days = int((sys_filtered["monitor_process_health"] != "healthy").sum())
    cols = st.columns(4)
    for col, label, value in zip(cols, ["API 오류율", "재시도율", "p95 응답", "모니터 이상 일수"], [f"{current['api_error_rate']:.1f}%", f"{current['retry_rate']:.1f}%", f"{current['p95_response_seconds']:.2f}초", f"{abnormal_days}일"]): col.metric(label, value)
    incidents = sys_filtered[sys_filtered["status"] != "normal"]
    signal("현재 상태" if incidents.empty else "확인 필요", "선택 기간에 기록된 시스템 이상이 없습니다." if incidents.empty else f"선택 기간에 시스템 이상 기록이 {len(incidents)}건 있습니다.", "good" if incidents.empty else "danger")
    left, right = st.columns(2)
    with left: st.caption("자원 사용 추이"); st.line_chart(sys_filtered.set_index("date")[["cpu_pct", "memory_pct", "disk_pct"]])
    with right: st.caption("응답 지연 추이"); st.line_chart(sys_filtered.set_index("date")[["api_latency_ms", "p95_response_ms"]])
    with st.expander("장애 상세 기록"): compact_table(incidents if not incidents.empty else sys_filtered.tail(1))
    st.subheader("실시간 운영"); render_live_panel()

with tabs[6]:
    hero("개선 Action", "도입 전 업무 부담과 도입 후 운영 데이터를 바탕으로 개선 결과와 다음 조치를 확인합니다.")
    st.markdown('<div class="action-heading">도입 전 · 도입 초기 · 3개월차 비교</div>', unsafe_allow_html=True)
    action_table(stage_compare)
    st.markdown('<div class="action-note">도입 후의 ‘직원→동료 재문의’ 건수는 챗봇 요청 수 × 동료 재문의율로 화면에서 계산한 값입니다. DB와 원본 데이터에는 추가하지 않았습니다.<br>도입 전은 사람을 통한 문의 결과, 도입 후는 챗봇 자체 해결 결과이므로 해결률을 동일한 성능 지표로 직접 비교하지 않습니다.</div>', unsafe_allow_html=True)
    time_cols = st.columns(4)
    time_cols[0].metric("도입 전 자료 검색", f"{base_m['avg_search_minutes']:.1f}분")
    time_cols[1].metric("도입 전 질문 작성", f"{base_m['avg_asking_minutes']:.1f}분")
    time_cols[2].metric("지원부서 답변 대기", f"{base_m['avg_support_response_wait_minutes']:.1f}분")
    time_cols[3].metric("지원부서 답변 작업", f"{base_m['avg_support_answering_minutes']:.1f}분")
    st.markdown('<div class="slide"><div class="slide-no">적용 결과</div><h2>문제 발견 → 원인 확인 → 조치 → 재측정</h2><p>반복 질문은 FAQ로, 사내 문서 질문은 RAG로, 피크 시간대 오류는 Retry 제한과 backoff로 개선했습니다.</p></div>', unsafe_allow_html=True)
    action_view = actions[["area", "issue", "action", "before", "after", "status"]].copy(); action_view.columns = ["영역", "발견한 문제", "적용한 조치", "개선 전", "개선 후", "상태"]
    action_table(action_view)
    st.markdown(f'<div class="slide"><div class="slide-no">운영 성과</div><h2>3개월 만에 개선 방향성을 확인했습니다</h2><div class="big-result">챗봇 해결률 {initial["resolution_rate"]:.1f}% → {month3["resolution_rate"]:.1f}%</div><p>재질문과 동료 재문의도 감소했습니다. 다만 아직 절반에 못 미치므로 <b>지속적인 지식 보완이 필요한 단계</b>입니다.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="slide"><div class="slide-no">다음 개선</div><h2>미해결 질문을 줄입니다</h2><p>낮은 해결률 Topic의 지식을 보강하고, RAG 검색 범위와 오류 원인을 조정한 뒤 같은 KPI로 다시 측정합니다.</p></div>', unsafe_allow_html=True)
    candidates = improvement_candidates(filtered)
    if not candidates.empty: st.subheader("자동 추출 개선 후보"); compact_table(candidates.head(5), height=240)
