# SOUNDWATCH

AI 기반 도시 소음 분석 및 모니터링 플랫폼. 음성 파일을 업로드하면 실제 오디오 특징과 분류 결과를 저장하고 지도·통계·관리자 검토 화면에서 확인합니다.

> 기본값은 특징 기반 **DEMO**입니다. 학습된 모델의 실제 추론이나 검증된 분류 정확도로 표시하지 않습니다. AI 결과는 환경소음 분류 보조 정보이며 법적·행정적 판정이 아닙니다. 음량은 장비 보정 없는 **dBFS 기반 상대 음량**입니다.

## 구현 기능

- JWT / Argon2 인증, USER·ADMIN 권한, 계정 활성화·역할 관리
- WAV·MP3·M4A·FLAC·OGG 업로드, 크기·MIME·디코딩·길이 검사
- mono 16kHz, RMS·peak·dBFS·무음 비율, 파형·log-mel 추출
- 재현 가능한 특징 기반 DEMO, 호환 ONNX MODEL 추론 인터페이스
- 작업 상태 DB 저장, WebSocket 전달과 API polling 복구
- 관리자 분류 수정·검토·실패 재분석·감사 로그
- 본인 기록 접근 통제, 원본 삭제, 기록 삭제 요청, 보존기간 정리
- Leaflet / OpenStreetMap, 마커 클러스터, 영역·날짜·유형·상태 필터
- 실제 API 기반 KPI·유형·시간대·요일·지역·일자 통계
- Alembic, SQLite / PostgreSQL 설정, Docker Compose, GitHub Actions

## 구조

```text
backend/app/       API, 인증, DB, 오디오, 추론, 작업 큐
backend/alembic/   스키마 마이그레이션
backend/tests/     단위·통합 테스트
frontend/src/      React 화면, 지도, 인증, API 및 테스트
scripts/           로컬 환경 초기화
docs/              설계·보안·모델·검증 문서
```

## 로컬 실행

Python 3.11, Node.js 22+, pnpm 10+를 준비합니다. FFmpeg가 PATH에 없으면 imageio-ffmpeg의 번들 실행 파일을 사용합니다.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python scripts/init_env.py
cd backend
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

새 터미널에서:

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

웹: http://localhost:5173 · API 문서: http://localhost:8000/docs

제한된 Windows 실행 환경에서 esbuild의 상위 경로 스캔이 차단되면, 빌드 결과로 시연할 수 있습니다:

```bash
pnpm build
pnpm preview --configLoader runner --port 5173
```

## 관리자·샘플 생성

활성화한 Python 환경에서 `backend` 폴더 기준:

```bash
python -m app.cli create-user --email YOUR_EMAIL --name YOUR_NAME --role ADMIN
python -m app.cli create-user --email USER_EMAIL --name USER_NAME --role USER
python -m app.cli seed --email YOUR_EMAIL
```

비밀번호는 프롬프트로 받습니다. 자동화 시 `SOUNDWATCH_USER_PASSWORD` 환경변수로 전달합니다. 기본 계정·비밀번호는 없습니다. seed는 합성 파형 5개를 생성해 실제 분석 파이프라인을 실행하며 제목에 합성 DEMO임을 표시합니다. 생성 음성과 DB는 Git에서 제외됩니다.

## Docker

Docker Engine / Docker Desktop과 Compose가 필요합니다.

```bash
python scripts/init_env.py
docker compose config --quiet
docker compose up --build --wait
docker compose exec backend python -m app.cli create-user --email YOUR_EMAIL --name YOUR_NAME --role ADMIN
docker compose exec backend python -m app.cli seed --email YOUR_EMAIL
```

웹: http://localhost:8080 · API: http://localhost:8000/docs

**개발 PC에서는 Docker Engine이 없어 전체 컨테이너 기동은 아직 검증하지 못했습니다.** CI에는 Compose build·기동·헬스체크가 구성되어 있으며 실제 실행 결과를 확인해야 합니다.

## 환경변수

`.env.example`은 설정 예시입니다. `scripts/init_env.py`가 임의의 JWT·DB 비밀값을 생성하며 기존 `.env`는 덮어쓰지 않습니다.

| 변수 | 용도 |
|---|---|
| DATABASE_URL | 로컬 SQLite 또는 PostgreSQL SQLAlchemy URL |
| JWT_SECRET | 32자 이상 비밀값 |
| CORS_ORIGINS | 허용 origin JSON 배열 |
| STORAGE_DIR | 비공개 원본 저장소 |
| INFERENCE_MODE | DEMO 또는 MODEL |
| MODEL_PATH / MODEL_NAME / MODEL_VERSION | 호환 ONNX 파일 및 버전 |
| CONFIDENCE_THRESHOLD | 검토 필요 임계값, 기본 0.55 |
| MAX_UPLOAD_MB / MAX_DURATION_SECONDS | 기본 20MB / 120초 |
| ORIGINAL_RETENTION_DAYS / RESULT_RETENTION_DAYS | 기본 7일 / 90일 |
| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | Compose DB 설정 |

## 테스트와 검증

```bash
cd backend
pytest --cov=app --cov-report=term-missing
ruff check .
cd ../frontend
pnpm test
pnpm typecheck
pnpm build
```

확인된 결과: Python 3.11.12 백엔드 23/23 통과, 프론트엔드 7/7 통과, TypeScript 및 프로덕션 빌드 통과. 최초 Python 3.12 실행의 커버리지는 84%입니다. 정확한 최종 검증 범위와 제한은 [테스트 보고서](docs/test-report.md)를 참고하세요.

## 사용자 흐름

가입·로그인 → 파일·위치·시각·공개 동의 등록 → 진행 상태 → 결과·파형 확인 → 이력·지도·통계 탐색 → 필요 시 관리자 검토 또는 삭제 요청.

원본 삭제 시 비동의 기록은 결과·위치 메타데이터도 삭제합니다. 동의 기록은 좌표·시각·텍스트를 축소하고 파형·스펙트로그램을 제거해 수치 특징을 유지합니다. 소유자 연결은 접근 통제를 위해 남으므로 내부 DB가 완전 익명이라는 의미는 아닙니다.

## 모델·성과 지표

MODEL은 `[1,160000]` float32 파형을 받아 `[1,10]` logits를 내는 호환 ONNX 파일을 필요로 합니다. YAMNet/PANNs 원본을 그대로 넣을 수 없으며 입력·출력 및 클래스 매핑 어댑터가 필요합니다. 모델 부재·계약 위반 시 서버는 유지되고 작업이 실패로 기록됩니다.

분류 정확도·macro F1은 **측정 전**입니다. 합성 음성은 정확도 평가 데이터가 아닙니다. 처리 성공률·평균 처리 시간·추론 시간·검토 비율·관리자 일치율은 DB에서 계산합니다. 테스트 통과율·커버리지 자동 수집은 아직 대시보드에 연결하지 않았습니다.

## 화면 예시

실제 랜딩 화면의 브라우저 표시를 확인했습니다. 배포·시연 후 개인정보를 제거한 스크린샷을 `docs/screenshots/`에 추가할 수 있습니다. 관리자·지도 화면의 전체 브라우저 E2E 검증은 남아 있습니다.

## 공개 데이터와 확장

공개 음성은 저장소에 포함하지 않습니다. [AudioSet](https://research.google.com/audioset/about.html), [PANNs](https://github.com/qiuqiangkong/audioset_tagging_cnn)의 원본 안내에서 다운로드 경로와 모델·개별 음원의 라이선스를 각각 확인하세요. 데이터셋 라벨 라이선스와 원본 음성 재배포 권한은 별개입니다.

우선순위: 실제 모델 어댑터·검증 데이터셋 평가 → Docker/PostgreSQL·브라우저 E2E → Celery/Redis, 서버 측 집계·운영 관측 강화.

자체 소스는 MIT 라이선스입니다. 외부 모델·데이터·라이브러리는 각 라이선스를 따릅니다.
