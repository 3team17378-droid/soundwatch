# 검증 기록

- Python 3.11.12 / Windows: pytest 23개 통과, 실패 0, 실행 10.20초 (2026-09-16 재검증).
- Python 3.12.14 / Windows 최초 실행: pytest 23개 통과, statements coverage 84%.
- React Vitest / Testing Library: 7개 통과.
- TypeScript 타입 검사: 통과.
- Vite 프로덕션 빌드: 통과. 초기 번들 약 903kB이며 분할 최적화 필요.
- Ruff: 통과한 검사 후 코드 포맷·보존 정책 변경이 있어 게시 전 재검사합니다.
- 브라우저: 랜딩·로그인 화면 표시 확인. 전체 E2E는 미완료.
- Docker Engine 미설치: Compose 전체 기동 / PostgreSQL 통합 검증 미완료.
- 실제 학습 모델, 정확도, macro F1: 미측정.

백엔드 테스트는 인증·JWT·RBAC·파일 검사·손상 처리·특징값·DEMO 재현성·IDOR·지도 비식별화·통계·검토·감사·삭제·재분석·WebSocket·롤백·보존 정책을 검증합니다. 프론트엔드는 보호 라우트, 파일 검사, 필터, 오류, DEMO 표시를 검증합니다. 일부 라이브러리의 deprecation 경고가 남아 있습니다.
