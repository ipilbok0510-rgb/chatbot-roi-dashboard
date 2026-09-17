"""실제 LLM API 없이 실시간 저장/집계/이상치 흐름을 확인하는 개발용 스크립트."""
from pathlib import Path
import argparse
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from monitoring.live_store import log_chat_usage


def create_normal_logs(count: int = 10) -> None:
    departments = ["개발", "IT운영", "영업", "기획", "인사", "재무"]
    for i in range(count):
        source = "RAG" if i % 3 == 0 else ("FAQ" if i % 3 == 1 else "LLM")
        use_api = source in {"RAG", "LLM"}
        inp = random.randint(700, 1800) if use_api else 0
        out = random.randint(150, 450) if use_api else 0
        log_chat_usage(
            employee_id=f"E{1000+i:04d}", employee_department=random.choice(departments),
            category="IT", topic="개발 시뮬레이션", question_text="개발용 정상 사용 시뮬레이션",
            question_type="simulated", route=source, answer_source=source,
            knowledge_version="demo_v1" if source == "RAG" else "", api_required=int(use_api),
            user_confirmed_resolved=1 if i % 4 else 0,
            resolution_type="chatbot" if i % 4 else "coworker",
            peer_reask=1 if i % 4 == 0 else 0,
            input_tokens=inp, output_tokens=out, api_call_count=int(use_api),
            status_code=200 if use_api else 0, api_cost_krw=round((inp+out)*0.002, 2),
        )


def create_anomaly_logs() -> None:
    for i in range(6):
        log_chat_usage(
            employee_id="E9999", employee_department="IT운영", category="IT", topic="이상치 시뮬레이션",
            question_text="개발용 이상치 테스트", question_type="simulated", route="RAG", answer_source="RAG",
            knowledge_version="oversized_context_v1", api_required=1,
            user_confirmed_resolved=0 if i < 4 else 1,
            resolution_type="coworker" if i < 4 else "chatbot", peer_reask=1 if i < 4 else 0,
            input_tokens=6500+i*500, output_tokens=1200, api_call_count=2 if i < 3 else 1,
            retry_count=1 if i < 5 else 0, status_code=504 if i == 0 else 200,
            error_type="timeout" if i == 0 else None, api_cost_krw=35+i,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--anomaly", action="store_true")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    create_normal_logs(args.count)
    if args.anomaly:
        create_anomaly_logs()
    print("개발용 실시간 로그 저장 완료")
