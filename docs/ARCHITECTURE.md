# 아키텍처

```text
직원
 ↓
employee_chatbot.py
 ↓
Router
 ├─ RULE: 권한/보안 별도절차, 명백한 잡담
 ├─ FAQ: 정형 반복질문
 ├─ RAG: 권한 확인 → 사내 문서 검색 → 관련 Chunk
 └─ LLM: 복합 업무 질문
 ↓
사용자 해결 여부/후속행동 피드백
 ↓
SQLite 즉시 저장
 ↓
1시간 단위 운영 집계
 ↓
KPI / 이상치 / 오류 분석
 ↓
app.py 관리자 대시보드
 ↓
문제 발견 → FAQ/RAG/API/시스템 개선
 ↓
동일 KPI 재측정
```

핵심은 단방향 대시보드가 아니라 **Feedback Loop**다.
