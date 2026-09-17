import re
import pandas as pd
from rag.retriever import rag_answer

SECURITY_WORDS = {
    "관리자 권한", "root", "비밀번호 알려", "보안 해제", "방화벽 해제", "접근 권한",
}

NON_WORK_PATTERNS = (
    r"^(나\s*)?심심(해|하다|한데|해요|합니다)?$",
    r"^(나랑\s*)?놀자$",
    r"^(너\s*)?(지금\s*)?뭐해$",
    r"^(재밌는|웃긴)\s*(얘기|이야기)(\s*(해줘|들려줘))?$",
    r"^끝말잇기(\s*하자)?$",
    r"^농담(\s*(하나\s*)?해줘)?$",
)


def _norm(text: str) -> str:
    q = re.sub(r"\s+", " ", (text or "").strip().lower())
    return re.sub(r"[?.!~]+$", "", q).strip()


def _is_obvious_non_work(q: str) -> bool:
    return any(re.fullmatch(pattern, q) for pattern in NON_WORK_PATTERNS)


def _result(**kwargs) -> dict:
    base = {
        "route": "UNKNOWN", "answer": "", "use_api": False, "anomaly": False,
        "department": "미분류", "category": "미분류", "topic": "미분류",
        "answer_source": "RULE", "knowledge_version": "",
    }
    base.update(kwargs)
    return base


def menu_answer(menu_id: str, faq_df: pd.DataFrame) -> dict:
    row = faq_df[faq_df["menu_id"] == menu_id]
    if row.empty:
        return _result(route="UNKNOWN_MENU", answer="등록되지 않은 메뉴입니다.")
    item = row.iloc[0]
    if item["sensitivity"] == "restricted":
        return _result(
            route="SECURITY_PROCEDURE", answer=str(item["answer"]), answer_source="RULE",
            department=str(item["department"]), category=str(item["category"]), topic=str(item["category"]),
        )
    return _result(
        route="FAQ", answer=str(item["answer"]), answer_source="FAQ",
        department=str(item["department"]), category=str(item["department"]), topic=str(item["category"]),
        knowledge_version=f"faq_{item['menu_id']}_v1",
    )


def route_question(question: str, faq_df: pd.DataFrame, employee_department: str = "일반", role: str = "employee") -> dict:
    q = _norm(question)
    if not q:
        return _result(route="EMPTY", answer="질문을 입력해주세요.")

    # 1. 권한/보안 변경은 챗봇이 직접 수행하지 않는다.
    if any(word in q for word in SECURITY_WORDS):
        return _result(
            route="SECURITY_PROCEDURE",
            answer="보안 또는 권한 변경 요청은 챗봇이 직접 처리하지 않습니다. 사내 권한신청 절차 또는 담당자에게 문의하세요.",
            answer_source="RULE", department="보안", category="일반규정", topic="권한/보안",
        )

    # 2. 반복·정형 질문은 FAQ로 우선 처리한다.
    best = None
    best_score = 0
    for _, row in faq_df.iterrows():
        kws = [k.strip().lower() for k in str(row["keywords"]).split(",") if k.strip()]
        score = sum(1 for k in kws if k in q)
        if score > best_score:
            best_score = score
            best = row
    if best is not None and best_score > 0:
        if best["sensitivity"] == "restricted":
            return _result(
                route="SECURITY_PROCEDURE", answer=str(best["answer"]), answer_source="RULE",
                department=str(best["department"]), category=str(best["department"]), topic=str(best["category"]),
            )
        return _result(
            route="FAQ", answer=str(best["answer"]), answer_source="FAQ",
            department=str(best["department"]), category=str(best["department"]), topic=str(best["category"]),
            knowledge_version=f"faq_{best['menu_id']}_v1",
        )

    # 3. 명백한 잡담만 업무 외로 차단한다.
    if _is_obvious_non_work(q):
        return _result(
            route="NON_WORK", answer="사내 업무 지원용 챗봇입니다. 업무와 무관한 잡담이나 놀이 요청에는 답변하지 않습니다.",
            answer_source="RULE", anomaly=True, category="업무외", topic="명백한 잡담",
        )

    # 4. 사내 문서에서 찾을 수 있으면 권한 기반 RAG로 처리한다.
    rag = rag_answer(question, employee_department=employee_department, role=role)
    if rag:
        return _result(
            route="RAG", answer=rag["answer"], use_api=True, answer_source="RAG",
            department=employee_department, category="사내문서", topic="RAG 검색",
            knowledge_version=rag["knowledge_version"],
        )

    # 5. 나머지 업무 질문은 LLM 대상으로 넘긴다.
    return _result(
        route="LLM", answer=(
            "FAQ와 현재 등록된 사내 문서만으로는 충분한 답변을 찾기 어렵습니다. "
            "실제 운영에서는 LLM API로 전달합니다. 데모에서는 실제 API 호출을 생략합니다."
        ), use_api=True, answer_source="LLM", department=employee_department, category="복합업무", topic="LLM 업무문의",
    )
