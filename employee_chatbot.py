from pathlib import Path
import time
import pandas as pd
import streamlit as st

from chatbot.router import menu_answer, route_question
from monitoring.live_store import log_chat_usage, update_request_feedback

ROOT = Path(__file__).resolve().parent
FAQ_PATH = ROOT / "data" / "faq.csv"

st.set_page_config(page_title="사내 업무 도우미", page_icon="💬", layout="centered")

st.markdown(
    """
    <style>
    .block-container {max-width: 900px; padding-top: 1.4rem; padding-bottom: 5rem;}
    [data-testid="stSidebar"] {background: #f7f8fa;}
    .chat-header {border:1px solid #e5e7eb;border-radius:18px;padding:18px 20px;margin-bottom:18px;background:white;box-shadow:0 4px 18px rgba(0,0,0,.04);}
    .chat-title {font-size:1.35rem;font-weight:700;margin-bottom:4px;}
    .chat-subtitle {color:#6b7280;font-size:.92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_faq() -> pd.DataFrame:
    return pd.read_csv(FAQ_PATH)


def route_label(result: dict) -> str:
    labels = {
        "FAQ": "FAQ 자동 답변 · LLM API 미사용",
        "RAG": "사내 문서 RAG · 실제 운영 시 LLM API 사용",
        "LLM": "복합 업무 질문 · 실제 운영 시 LLM API 사용",
        "SECURITY_PROCEDURE": "권한/보안 요청 · 별도 절차 안내",
        "NON_WORK": "명백한 업무 외 질문 · API 미사용",
    }
    return labels.get(result.get("route"), result.get("route", ""))


def save_usage(employee_id: str, employee_department: str, user_text: str, result: dict, question_type: str, elapsed: float) -> str:
    # 현재 데모는 실제 LLM API를 호출하지 않으므로 Token/API usage는 0으로 저장한다.
    # 실제 API 연동 후에는 응답 usage 메타데이터를 아래 필드에 전달하면 된다.
    return log_chat_usage(
        employee_id=employee_id,
        employee_department=employee_department,
        category=result.get("category", "미분류"),
        topic=result.get("topic", "미분류"),
        question_text=user_text,
        question_type=question_type,
        route=result.get("route", "UNKNOWN"),
        answer_source=result.get("answer_source", "UNKNOWN"),
        knowledge_version=result.get("knowledge_version", ""),
        api_required=int(bool(result.get("use_api"))),
        user_confirmed_resolved=-1,
        resolution_type="pending",
        response_seconds=elapsed,
        input_tokens=0,
        output_tokens=0,
        api_call_count=0,
        retry_count=0,
        status_code=0,
        error_type=None,
        api_cost_krw=0.0,
        anomaly_flag=int(bool(result.get("anomaly"))),
    )


def add_exchange(user_text: str, result: dict, request_id: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.messages.append({
        "role": "assistant", "content": result["answer"], "meta": route_label(result),
        "request_id": request_id, "feedback_state": "pending",
    })


def mark_feedback(msg_index: int, request_id: str, resolved: int, resolution_type: str, peer_reask: int = 0, recontact: int = 0) -> None:
    update_request_feedback(
        request_id,
        resolved=resolved,
        resolution_type=resolution_type,
        peer_reask=peer_reask,
        recontact_within_24h=recontact,
    )
    st.session_state.messages[msg_index]["feedback_state"] = "done"
    st.session_state.messages[msg_index]["feedback_text"] = "피드백이 저장되었습니다."


faq = load_faq()
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "안녕하세요. 사내 업무 도우미입니다. 자주 찾는 메뉴를 누르거나 업무 관련 질문을 입력해주세요.",
        "meta": "FAQ → 권한 기반 RAG → LLM 순으로 처리합니다.",
    }]

with st.sidebar:
    st.header("직원용 챗봇")
    employee_id = st.text_input("직원 ID (데모)", value="E0001")
    employee_department = st.selectbox("소속 부서", ["개발", "IT운영", "영업", "기획", "인사", "재무", "디자인", "고객지원"])
    st.caption("실제 회사에서는 SSO의 사용자/부서 정보를 사용합니다.")
    st.markdown("**운영 원칙**")
    st.write("• 질문마다 사용 로그 즉시 저장")
    st.write("• 반복 정형 질문은 FAQ")
    st.write("• 내부 문서는 권한 확인 후 RAG")
    st.write("• 명백한 잡담만 API 전 차단")
    st.write("• 답변 후 실제 해결 여부를 사용자에게 확인")
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = st.session_state.messages[:1]
        st.rerun()

st.markdown(
    '<div class="chat-header"><div class="chat-title">💬 사내 업무 도우미</div><div class="chat-subtitle">FAQ · 사내 지식(RAG) · LLM을 상황에 맞게 사용합니다.</div></div>',
    unsafe_allow_html=True,
)

st.markdown("**자주 찾는 메뉴**")
menu_rows = faq.head(8).reset_index(drop=True)
cols = st.columns(4)
for i, row in menu_rows.iterrows():
    label = f"{row['department']} · {row['category']}"
    if cols[i % 4].button(label, key=f"quick_{row['menu_id']}", use_container_width=True):
        started = time.perf_counter()
        result = menu_answer(row["menu_id"], faq)
        elapsed = time.perf_counter() - started
        rid = save_usage(employee_id, employee_department, label, result, "menu", elapsed)
        add_exchange(label, result, rid)
        st.rerun()

st.divider()

for idx, msg in enumerate(st.session_state.messages):
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("meta"):
            st.caption(msg["meta"])
        rid = msg.get("request_id")
        if rid and msg.get("feedback_state") == "pending":
            st.caption("이 답변으로 업무 문제를 해결했나요?")
            c1, c2 = st.columns(2)
            if c1.button("✅ 해결됨", key=f"resolved_{rid}", use_container_width=True):
                mark_feedback(idx, rid, 1, "chatbot")
                st.rerun()
            if c2.button("❌ 해결되지 않음", key=f"unresolved_{rid}", use_container_width=True):
                st.session_state.messages[idx]["feedback_state"] = "choose_followup"
                st.rerun()
        elif rid and msg.get("feedback_state") == "choose_followup":
            st.caption("이후 어떻게 해결했나요?")
            c1, c2, c3 = st.columns(3)
            if c1.button("동료/사수 문의", key=f"coworker_{rid}"):
                mark_feedback(idx, rid, 0, "coworker", peer_reask=1)
                st.rerun()
            if c2.button("담당부서 문의", key=f"department_{rid}"):
                mark_feedback(idx, rid, 0, "department")
                st.rerun()
            if c3.button("사내 문서 검색", key=f"document_{rid}"):
                mark_feedback(idx, rid, 0, "document")
                st.rerun()
            c4, c5 = st.columns(2)
            if c4.button("다시 챗봇 질문", key=f"reask_{rid}"):
                mark_feedback(idx, rid, 0, "chatbot_reask", recontact=1)
                st.rerun()
            if c5.button("아직 미해결", key=f"still_{rid}"):
                mark_feedback(idx, rid, 0, "unresolved")
                st.rerun()
        elif msg.get("feedback_text"):
            st.caption("✓ " + msg["feedback_text"])

question = st.chat_input("업무 관련 질문을 입력하세요. 예: Mac VPN 설정 방법 알려줘")
if question:
    started = time.perf_counter()
    result = route_question(question, faq, employee_department=employee_department)
    elapsed = time.perf_counter() - started
    rid = save_usage(employee_id, employee_department, question, result, "text", elapsed)
    add_exchange(question, result, rid)
    st.rerun()
