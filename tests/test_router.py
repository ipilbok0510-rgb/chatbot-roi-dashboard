from pathlib import Path
import pandas as pd
from chatbot.router import route_question

ROOT = Path(__file__).resolve().parents[1]
FAQ = pd.read_csv(ROOT / "data" / "faq.csv")


def test_faq_route():
    r = route_question("월급 명세서 어디서 봐?", FAQ, employee_department="개발")
    assert r["answer_source"] == "FAQ"
    assert r["use_api"] is False


def test_non_work_is_conservative():
    r = route_question("심심해", FAQ, employee_department="개발")
    assert r["route"] == "NON_WORK"
    r2 = route_question("인터넷 연결이 안돼", FAQ, employee_department="개발")
    assert r2["route"] != "NON_WORK"


def test_rag_route():
    r = route_question("Mac VPN 설정 방법 알려줘", FAQ, employee_department="개발")
    assert r["answer_source"] in {"FAQ", "RAG"}
