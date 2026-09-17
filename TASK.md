# TASK — 1인 개발 순서

## 1. 기준 데이터 고정
- [x] 가상회사 직원 300명
- [x] 도입 전 월 문의 250건
- [x] 초기 1개월 요청 600건 / 해결률 30.0%
- [x] 2개월차 요청 720건 / 해결률 37.1%
- [x] 3개월차 요청 850건 / 해결률 45.1%
- [x] Excel 통합본 제거, CSV + SQLite만 사용

## 2. 데이터/DB
- [x] `baseline_peer_inquiries.csv`
- [x] `chatbot_requests.csv`
- [x] `kpi_period_summary.csv`
- [x] `company_profile.csv`
- [x] `improvement_actions.csv`
- [x] `system_metrics.csv`
- [x] `scripts/build_db.py`

## 3. 직원 챗봇
- [x] FAQ 우선
- [x] 명백한 잡담만 차단
- [x] 권한/보안 요청은 별도 절차 안내
- [x] 권한 기반 RAG 데모
- [x] 미일치 질문은 LLM 대상으로 분류
- [x] 답변 후 해결 여부/후속 행동 저장

## 4. 관리자 대시보드
- [x] 운영 요약
- [x] 초기 vs 3개월
- [x] 질문/해결 분석
- [x] FAQ/RAG/LLM 분석
- [x] Token/API
- [x] 시스템/오류
- [x] 개선 Action

## 5. 실시간 운영
- [x] 직원 사용 시 DB 즉시 저장
- [x] 개발 1분 / 운영 1시간 집계
- [x] 이상치 탐지
- [x] Webhook/이메일 알림 선택

## 6. 검증
- [ ] `python scripts/generate_test_data.py`
- [ ] `python scripts/build_db.py`
- [ ] `python -m pytest -q`
- [ ] 직원 챗봇 UI 수동 테스트
- [ ] 관리자 대시보드 7개 탭 수동 테스트
- [ ] `python scripts/simulate_live_usage.py --anomaly`
- [ ] `python scripts/hourly_monitor.py --once`

## 7. 발표 전
- [ ] `MONITOR_INTERVAL_SECONDS = 3600` 여부 결정
- [ ] `docs/PRESENTATION_5MIN.md` 리허설
- [ ] `docs/QNA.md` 확인
