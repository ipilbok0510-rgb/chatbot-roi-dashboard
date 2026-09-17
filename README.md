# 사내 AI 챗봇 운영 효율 개선 모니터링 시스템

사내 AI 챗봇을 하나의 **운영 서비스**로 보고, 질문 해결 품질·FAQ/RAG 활용·LLM API 사용·Token·응답시간·오류·시스템 상태를 함께 모니터링하여 운영 데이터를 기반으로 지속적으로 개선하는 프로젝트입니다.

> 모든 회사 정보와 성과 수치는 프로젝트 검증을 위한 시뮬레이션입니다. 특정 기업의 실제 성과를 의미하지 않습니다.

## 1. 가상 회사

- 회사명: **GaonWorks Services**
- 업종: IT 서비스 / B2B 운영 지원
- 직원 수: **300명**
- 근무지: 서울 본사 + 1개 지사
- 주요 문의: IT, 인사, 총무, 재무, 사내 일반 규정

약 200~1,000명 규모에서 반복 문의와 내부 문서가 많고, 외부 AI에 사내 문서를 그대로 제공하기 어려운 조직을 적용 후보로 가정했습니다.

## 2. 문제 정의

챗봇 도입 전에는 직원이 필요한 정보를 찾지 못하면 동료·사수·지원부서에 직접 문의한다고 가정합니다.

도입 전 1개월 baseline은 월 **250건**입니다.

- 자료 검색: 평균 6.7분
- 질문 작성/전달: 평균 2.0분
- 지원부서에 문의했을 때 질문자가 답변을 받을 때까지의 대기시간: 평균 41.8분
- 지원부서 직원이 실제 답변 작성에 사용한 시간: 평균 9.3분

`response_wait_minutes`는 **질문한 직원이 답변을 받을 때까지 기다린 전체 경과시간**이며, 지원부서의 실제 작업시간인 `answering_minutes`와 구분합니다.

## 3. 프로젝트 가설

챗봇은 도입 직후부터 높은 성과를 내는 것이 아니라, 실제 사용 데이터를 모니터링하고 문제를 개선하면서 점진적으로 효율이 높아진다고 가정합니다.

### 초기 1개월

- 요청 600건
- 챗봇 해결률 30.0%
- FAQ 처리율 8.0%
- RAG 처리율 12.0%
- LLM 호출률 84.0%
- 재질문율 38.0%
- 동료 재문의율 28.0% (168건·계산값)

### 3개월차

- 요청 850건
- 챗봇 해결률 45.1%
- FAQ 처리율 18.0%
- RAG 처리율 24.0%
- RAG 내부 해결률 65.2%
- LLM 호출률 74.0%
- 재질문율 28.0%
- 동료 재문의율 16.0% (136건·계산값)

3개월 만에 완성된 서비스가 되었다고 가정하지 않습니다. **소폭 개선이 확인되었고, 장기 운영에서 추가 개선 여지가 남아 있는 상태**로 설계했습니다.

## 4. 질문 처리 구조

```text
직원 질문
   ↓
권한/보안 변경 요청? ── YES → 별도 회사 절차 안내
   ↓ NO
FAQ 일치? ─────────── YES → FAQ 답변 / LLM 호출 없음
   ↓ NO
명백한 잡담? ───────── YES → 업무용 챗봇 안내 / API 호출 없음
   ↓ NO
사내 문서 검색 가능? ── YES → 권한 기반 RAG → 필요한 Chunk만 LLM Context
   ↓ NO
복합 업무 질문 ──────────────→ LLM
```

RAG는 사내 문서를 사용할 수 있다는 점에서 사내용 챗봇의 핵심 기능입니다. 단, RAG 자체가 보안을 보장하는 것은 아니므로 사용자 인증·문서 접근권한·로그 최소화가 함께 필요합니다.

## 5. 사용자 결과 확인

챗봇이 답변을 생성했다고 해서 해결로 처리하지 않습니다.

직원용 챗봇에서 답변 후:

```text
이 답변으로 해결되었나요?
[해결됨] [해결되지 않음]

미해결 시:
[동료/사수 문의]
[담당부서 문의]
[사내 문서 검색]
[다시 챗봇 질문]
[아직 미해결]
```

을 기록합니다.

## 6. 관리자 대시보드

`app.py`는 7개 탭으로 구성합니다.

1. **운영 요약** — 현재 요청·해결률·재질문·동료 재문의·LLM 호출 등 핵심 상태
2. **초기 vs 3개월** — 초기 1개월과 3개월차 KPI 비교
3. **질문/해결 분석** — 카테고리·Topic별 해결률과 후속 행동
4. **FAQ/RAG/LLM 분석** — 각 처리 방식의 비중·해결률·지식 버전
5. **Token/API** — Token/Request, Token/해결건, Retry, 비용
6. **시스템/오류** — CPU/Memory/Latency/429/Timeout/DB·로그 오류/실시간 알림
7. **개선 Action** — 문제 → 원인 → 조치 → 재측정 기록

## 7. 핵심 KPI

### 업무 효율
- Chatbot Resolution Rate
- Recontact Rate
- Peer Re-ask Rate
- Resolution Time

### AI 처리 효율
- FAQ Hit Rate
- RAG Route / Resolution Rate
- LLM Call Rate
- Token / Request
- Token / Resolved Request

### 시스템 안정성
- API Error Rate
- Retry Rate
- p95 Response Time
- DB Write Failure
- Log Collection Failure
- CPU / Memory / Disk

비용은 `API Cost / Request`와 `API Cost / Resolved Request`로 보되 **주목적이 아닌 보조 지표**로 사용합니다.

## 8. 실시간 저장과 주기 집계

직원 질문은 즉시 SQLite의 실시간 로그 테이블에 저장합니다. 운영 집계와 이상치 분석은 기본적으로 1시간 단위로 수행합니다.

개발 중에는 1분으로 설정되어 있습니다.

`monitoring/config.py`

```python
# 개발 테스트: 1분
MONITOR_INTERVAL_SECONDS = 60

# ★ 발표/운영에서 1시간으로 변경
# MONITOR_INTERVAL_SECONDS = 3600
```

## 9. 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_test_data.py
python scripts/build_db.py
```

직원용 챗봇:

```bash
streamlit run employee_chatbot.py --server.port 8501
```

관리자 대시보드:

```bash
streamlit run app.py --server.port 8502
```

주기 모니터:

```bash
python scripts/hourly_monitor.py
```

개발용 이상치 테스트:

```bash
python scripts/simulate_live_usage.py --anomaly
```

## 10. 데이터 형식

프로젝트 데이터는 **CSV + SQLite**를 기준으로 사용합니다.

- CSV: 사람이 확인하기 쉽고 Git diff가 가능하며 파일이 가벼움
- SQLite `.db`: 실제 쿼리·대시보드·실시간 로그 처리용

별도의 통합 Excel 파일은 만들지 않습니다. 같은 데이터를 중복 보관하고 용량과 관리 포인트를 늘릴 필요가 없기 때문입니다.

## 11. 최종 결론

이 프로젝트의 결론은 "챗봇 도입으로 큰 효과가 이미 증명되었다"가 아닙니다.

> 챗봇 도입 후 사용 기록을 모니터링하고 FAQ·RAG 지식·API 운영을 개선하면서 초기 1개월보다 3개월차의 해결률이 30.0%에서 45.1%로 상승했고, 재질문과 동료 재문의도 감소하는 시뮬레이션 결과가 나타났습니다. 아직 3개월이라 개선 폭은 제한적이고 미해결 비율도 높지만, 장기적으로 같은 대시보드에서 문제를 발견하고 개선·재측정을 반복하면 더 효율적인 사내 AI 서비스로 발전할 수 있다는 운영 구조를 보여주는 것이 목적입니다.

자세한 문서는 `docs/`를 참고하세요.
