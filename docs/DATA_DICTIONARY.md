# 데이터 정의서

## baseline_peer_inquiries

| 컬럼 | 의미 |
|---|---|
| inquiry_id | 도입 전 문의 식별자 |
| created_at | 문의 발생 시각 |
| employee_id | 질문한 직원의 익명 ID |
| employee_department | 질문한 직원의 소속 부서 |
| support_department | 지원부서 문의일 때 담당 지원부서 |
| category / topic | 질문 분야 / 세부 주제 |
| source | support_department / coworker / senior / internal_document |
| search_minutes | 문의 전 혼자 자료를 찾은 시간 |
| asking_minutes | 질문 작성·전달에 사용한 시간 |
| response_wait_minutes | **질문한 직원이 질문을 보낸 후 최종 답변을 받을 때까지의 경과시간** |
| answering_minutes | 상대방이 실제 답변 작업에 사용한 시간 |
| resolved | 최종 해결 여부 |
| period | pre_chatbot_1m |

`response_wait_minutes`와 `answering_minutes`는 서로 다른 지표다.

## chatbot_requests

| 컬럼 | 의미 |
|---|---|
| request_id | 업무 요청 식별자 |
| conversation_id | 대화 식별자 |
| period | initial_1m / month2 / month3 |
| employee_id | 익명 직원 ID |
| employee_department | 직원 소속 |
| category / topic | 질문 분야 / 주제 |
| question_text | 테스트용 질문 |
| route / answer_source | FAQ / RAG / LLM / RULE |
| knowledge_version | 사용된 FAQ/사내문서 버전 |
| user_confirmed_resolved | 사용자가 확인한 해결 여부 |
| resolution_type | chatbot / coworker / department / document / unresolved 등 |
| recontact_within_24h | 같은 문제를 다시 질문했는지 |
| peer_reask | 결국 동료/사수에게 다시 물어봤는지 |
| feedback_score | 사용자 평가 |
| response_seconds | 응답시간 |
| input_tokens / output_tokens | LLM Token |
| api_call_count | Retry 포함 API 호출수 |
| retry_count | 재시도 횟수 |
| status_code / error_type | API 결과 |
| api_cost_krw | 프로젝트 가정 단가 기반 API 비용 |

## system_metrics
성과 KPI가 아니라 장애 원인 확인용 보조지표다. CPU, Memory, Disk, API latency, p95, 오류, DB/로그 실패, 모니터 프로세스 상태를 기록한다.
