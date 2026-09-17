# LLM/API 자원 효율화 전략

목표는 LLM 사용을 무조건 최소화하는 것이 아니라 **답변 품질을 유지하면서 불필요한 호출과 Token 소비를 줄이는 것**이다.

```text
질문
 ↓
FAQ
 ↓ 실패
RAG
 ↓ 부족
LLM
```

개선 방법:
- 반복 정형 질문은 관리자 검토 후 FAQ 등록
- RAG는 권한 있는 문서만 검색
- Top-K와 Chunk 크기를 제한
- 오래된 대화 History는 요약
- 출력 길이 제한
- Retry 최대 횟수 제한
- 429/Timeout은 exponential backoff
- 실제 운영에서는 Cache와 모델 라우팅을 추가할 수 있음
