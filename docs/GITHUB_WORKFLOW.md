# GitHub 작업 방식 — 1인 개발

현재는 한 사람이 개발하므로 기능별 브랜치를 과도하게 나누지 않아도 된다.

권장:

```bash
git checkout -b feature/monitoring-v4
# 작업
git add .
git commit -m "feat: align dashboard with 3-month monitoring data"
git push -u origin feature/monitoring-v4
```

GitHub에서 PR로 main에 병합하면 변경 이력이 명확하다. 작은 문서 수정은 main에 직접 커밋해도 되지만, 대시보드/DB 구조 변경은 브랜치+PR을 권장한다.

`.venv`, `.env`, SQLite의 `*.db-wal`, `*.db-shm` 파일은 Git에 올리지 않는다.
