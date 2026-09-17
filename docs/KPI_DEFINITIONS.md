# KPI 정의

| KPI | 계산 | 해석 |
|---|---|---|
| Chatbot Resolution Rate | 사용자 해결 확인 / 전체 요청 | 챗봇이 실제 업무 목적을 해결했는가 |
| Recontact Rate | 24시간 내 동일 문제 재질문 / 전체 요청 | 답변이 충분했는가 |
| Peer Re-ask Rate | 동료/사수 재문의 / 전체 요청 | 기존 사람 문의가 실제로 줄고 있는가 |
| FAQ Hit Rate | FAQ 요청 / 전체 요청 | 반복 정형 질문 자동화 정도 |
| RAG Route Rate | RAG 요청 / 전체 요청 | 사내 지식 활용 범위 |
| RAG Resolution Rate | RAG 해결 / RAG 요청 | 사내 지식 품질과 검색 품질 |
| LLM Call Rate | LLM API가 호출된 요청 / 전체 요청 | RAG도 LLM 생성이 있으면 포함 |
| Token / Request | 총 Token / 전체 요청 | 요청 1건당 AI 자원 |
| Token / Resolved Request | 총 Token / 해결 요청 | 실제 해결 1건당 AI 자원 |
| Retry Rate | Retry 발생 API 요청 / API 요청 | API 안정성·Retry 설정 |
| API Error Rate | 실패 API 요청 / API 요청 | API 안정성 |
| p95 Response Time | 응답시간 95백분위 | 느린 사용자 경험 탐지 |

임계값은 프로젝트용 가정이며 실제 운영 시 조직별 정상범위를 별도로 산정한다.
