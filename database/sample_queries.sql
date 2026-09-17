-- 1) 기간별 요청/해결률
SELECT
    period,
    COUNT(*) AS requests,
    ROUND(AVG(user_confirmed_resolved) * 100, 1) AS resolution_rate
FROM chatbot_requests
GROUP BY period;

-- 2) 기간별 FAQ/RAG/LLM 비중
SELECT
    period,
    answer_source,
    COUNT(*) AS requests,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY period), 1) AS share_pct
FROM chatbot_requests
GROUP BY period, answer_source
ORDER BY period, requests DESC;

-- 3) 동료 재문의가 많은 Topic
SELECT
    category,
    topic,
    COUNT(*) AS requests,
    ROUND(AVG(peer_reask) * 100, 1) AS peer_reask_rate,
    ROUND(AVG(user_confirmed_resolved) * 100, 1) AS resolution_rate
FROM chatbot_requests
GROUP BY category, topic
ORDER BY peer_reask_rate DESC;

-- 4) Token / 해결건
SELECT
    period,
    SUM(input_tokens + output_tokens) AS total_tokens,
    SUM(user_confirmed_resolved) AS resolved_requests,
    ROUND(
        SUM(input_tokens + output_tokens) * 1.0 /
        NULLIF(SUM(user_confirmed_resolved), 0), 0
    ) AS tokens_per_resolved_request
FROM chatbot_requests
GROUP BY period;

-- 5) 도입 전 지원부서 답변 대기시간과 실제 답변 작업시간
SELECT
    ROUND(AVG(response_wait_minutes), 1) AS avg_employee_wait_minutes,
    ROUND(AVG(answering_minutes), 1) AS avg_support_work_minutes
FROM baseline_peer_inquiries
WHERE source = 'support_department';
