# 실시간 저장 / 주기 모니터링

## 흐름
```text
직원 질문
→ 원본 로그 즉시 SQLite 저장
→ 기본 1시간 단위 집계
→ 이상치 탐지
→ alert_history 저장
→ Webhook 우선 / 이메일 보조
→ 관리자 대시보드
```

개발 중에는 `monitoring/config.py`에서 60초로 설정한다.

```python
MONITOR_INTERVAL_SECONDS = 60
# 발표/운영: 3600
```

### 즉시 확인 가치가 높은 장애
- 대량 API 오류
- DB 저장 실패
- 서비스 장애
- 인증/권한 실패

### 주기적으로 볼 지표
- 해결률 감소
- 재질문 증가
- Token/Request 증가
- Retry 증가
- FAQ/RAG 처리 비율 변화

### 장기 개선 후보
- FAQ 후보
- 반복 미해결 Topic
- 오래된 문서
- 지식 부족 분야
