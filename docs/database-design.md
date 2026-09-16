# 데이터베이스

users → noise_records → analysis_results / analysis_jobs / reviews 관계입니다. audit_logs는 actor_id, target_type, target_id로 변경 대상을 추적합니다. UUID 문자열 PK와 SQLAlchemy 바인딩을 사용합니다.

noise_records.current_analysis_id와 current_job_id는 최신 시도를 가리킵니다. 과거 분석 결과는 재분석 시 삭제하지 않아 버전·오디오 hash·설정으로 추적합니다. reviews는 이전·확정 분류와 의견을 보존합니다. 좌표 원본과 공개 좌표는 별도 컬럼입니다.

Alembic 초기 migration은 테이블·인덱스를 명시적으로 생성합니다. `alembic upgrade head`로 적용하고 변경 시 `alembic revision --autogenerate -m 설명` 후 diff를 검토합니다. 자동 생성 코드를 무검토로 배포하지 않습니다. DB·원본 저장소는 Git에 포함하지 않습니다.
