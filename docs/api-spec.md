# API

실행 중 `/docs`와 `/openapi.json`이 전체 요청·응답 정의를 제공합니다. 기본 접두사는 `/api/v1`입니다.

| 영역 | 경로 | 권한 |
|---|---|---|
| 인증 | POST auth/register, auth/login; GET auth/me | 가입·로그인 공개 |
| 기록 | POST/GET noise-records; GET/DELETE noise-records/{id} | 본인 또는 관리자 |
| 원본 | GET/DELETE noise-records/{id}/audio | 본인 또는 관리자 |
| 재분석 | POST noise-records/{id}/reanalyze | 관리자, FAILED만 |
| 결과 | GET noise-records/{id}/analysis | 본인 또는 관리자 |
| 작업 | GET analysis/jobs/{id}; WS ws/analysis/{id} | 본인 또는 관리자 |
| 검토 | GET admin/noise-records; POST admin/noise-records/{id}/review | 관리자 |
| 사용자 | GET admin/users; PATCH admin/users/{id} | 관리자 |
| 감사 | GET admin/audit-logs | 관리자 |
| 통계 | GET dashboard/summary, timeseries, categories | 사용자 본인 / 관리자 전체 |
| 지도 | GET map/noise-events | 사용자 공개 동의 데이터 / 관리자 전체 |
| 모델 | GET system/model-status | 인증 사용자 |
| 운영 | GET /health, /ready | 공개 |

Bearer JWT 인증. WebSocket은 연결 후 첫 JSON 프레임 `{ "token": "..." }`으로 인증하고 URL에는 토큰을 넣지 않습니다. 업로드는 multipart이며 title, description, latitude, longitude, address, occurred_at(시간대 필수), public_consent, file을 받습니다. 목록은 page/page_size, 검색·정렬 및 날짜·유형·상태 필터를 지원합니다. DELETE 기록과 재분석은 reason을 포함한 JSON을 받습니다.
