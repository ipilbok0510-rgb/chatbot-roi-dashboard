# 시스템 엔지니어 점검표

| 현상 | 우선 확인 | 조치 예시 |
|---|---|---|
| 해결률 하락 | Topic, FAQ/RAG 지식 버전 | 문서/FAQ 보완 |
| 재질문 증가 | 반복 실패 질문 | 답변·지식 품질 확인 |
| Token/Request 급증 | RAG Top-K, Context, History | 검색 범위/Context 축소 |
| 429 증가 | 호출량, Rate Limit, Retry | Backoff, Queue, FAQ 전환 |
| Timeout | API latency, Context 크기, 네트워크 | Timeout/Retry 조정 |
| 5xx | 외부 API 상태 | 재시도 제한/장애 공지 |
| DB Write Failure | lock, disk, connection | 잠금/용량/연결 확인 |
| 로그 누락 | collector/monitor process | 프로세스 복구 |
| 특정 직원 Token 급증 | 요청수, 세션당 Token, Retry, RAG | 개인 문제로 단정하지 않고 시스템 원인부터 확인 |

CPU/Memory는 업무성과가 아니라 장애 원인 분석용 보조 지표다.
