# 관리자 대시보드 7개 탭 상세

## 1. 운영 요약
현재 서비스가 평소와 다른지 빠르게 보는 첫 화면.
- 요청 수
- 해결률
- 재질문율
- 동료 재문의율
- LLM 호출률
- Token/해결건
- 도입 전 baseline 대기시간/지원부서 답변 작업시간

## 2. 초기 vs 3개월
프로젝트 결론을 보여주는 비교 화면.
- 해결률 30.0% → 45.1%
- 재질문율 38.0% → 28.0%
- 동료 재문의율 44.0% → 32.0%
- FAQ 8.0% → 18.0%
- RAG 12.0% → 24.0%
- LLM 호출 84.0% → 74.0%
- Token/Request 1991 → 1391

3개월 만에 완성되었다고 해석하지 않고, **소폭 개선 + 추가 운영 필요**로 결론 낸다.

## 3. 질문/해결 분석
어떤 Topic이 챗봇을 힘들게 하는지 찾는다.
- 카테고리/Topic별 요청
- 해결률
- 재질문율
- 동료 재문의율
- 평균 응답시간
- 미해결 이후 행동

## 4. FAQ/RAG/LLM 분석
질문이 어떤 방식으로 처리되는지 확인한다.
- FAQ Hit Rate
- RAG Route Rate
- RAG Resolution Rate
- Direct LLM Rate
- Knowledge Version
- 처리 방식별 Token/API 사용

RAG도 생성 단계에서 LLM API를 사용하므로 LLM 호출률은 RAG + Direct LLM을 포함한다.

## 5. Token/API
AI 자원 효율을 확인한다.
- Token/Request
- Token/Resolved Request
- API Call Count
- Retry Rate
- API Cost/Request
- 직원별 Token은 **원인 Drill-down용**으로만 사용

## 6. 시스템/오류
장애 원인을 확인한다.
- CPU / Memory / Disk
- API latency / p95
- 429 / 500 / 504
- Retry
- DB Write Failure
- Log Collection Failure
- Monitoring Process Health
- 실시간 집계 및 알림

## 7. 개선 Action
모니터링 결과를 행동으로 연결한다.

| 발견 | 원인 | 조치 | 재측정 |
|---|---|---|---|
| 반복 연차 질문 | 정형 질문 | FAQ 등록 | FAQ Hit 상승 |
| Mac VPN 낮은 해결률 | 문서 부족 | Mac 문서 v2 추가 | RAG 해결률 상승 |
| RAG Token 증가 | Context 과다 | Top-K 축소 | Token/Request 감소 |
| 429/Timeout | 요청 집중 | Retry 제한/Backoff | 오류·Retry 감소 |
