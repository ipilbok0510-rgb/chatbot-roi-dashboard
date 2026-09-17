from monitoring.live_store import ensure_live_tables, log_chat_usage, update_request_feedback, read_live_logs


def test_live_log_and_feedback_roundtrip():
    ensure_live_tables()
    rid = log_chat_usage(
        employee_id="TEST001", employee_department="개발", category="IT", topic="테스트",
        question_text="테스트 질문", question_type="test", route="FAQ", answer_source="FAQ",
        api_required=0, user_confirmed_resolved=-1,
    )
    update_request_feedback(rid, resolved=1, resolution_type="chatbot")
    df = read_live_logs()
    row = df[df["request_id"] == rid].iloc[-1]
    assert int(row["user_confirmed_resolved"]) == 1
    assert row["resolution_type"] == "chatbot"
