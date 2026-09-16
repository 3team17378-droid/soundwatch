import asyncio
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, WebSocket
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audio import AudioError, decode, validate_header
from app.core.config import settings
from app.db import SessionLocal, get_db
from app.ml import CLASSES, model_status
from app.models import AnalysisResult, AuditLog, Job, NoiseRecord, Review, User, now, uid
from app.schemas import Login, Reason, Register, ReviewInput, UploadMetadata, UserPatch
from app.security import (
    admin,
    current_user,
    dummy_hash,
    password_hash,
    public_user,
    throttle,
    token_for,
    user_from_token,
)
from app.services import (
    audit,
    fields,
    purge_record,
    remove_original,
    remove_reconstructable_features,
    storage_path,
)

router = APIRouter(prefix="/api/v1")
NOTICE = "AI 결과는 환경소음 분류를 보조하는 참고 정보이며 법적·행정적 판정이 아닙니다. 음량은 dBFS 기반 상대 음량입니다."


@router.post("/auth/register", status_code=201, dependencies=[Depends(throttle)])
def register(body: Register, db: Session = Depends(get_db)):
    user = User(
        email=str(body.email).lower(), name=body.name, password_hash=password_hash.hash(body.password)
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 등록된 이메일입니다.")
    return public_user(user)


@router.post("/auth/login", dependencies=[Depends(throttle)])
def login(body: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    valid = password_hash.verify(body.password, user.password_hash if user else dummy_hash)
    if not user or not valid or not user.is_active:
        raise HTTPException(401, "이메일 또는 비밀번호가 올바르지 않습니다.")
    return {"access_token": token_for(user), "token_type": "bearer", "user": public_user(user)}


@router.get("/auth/me")
def me(user=Depends(current_user)):
    return public_user(user)


def owned(db, record_id, user, lock=False):
    query = select(NoiseRecord).where(NoiseRecord.id == record_id)
    if lock:
        query = query.with_for_update()
    record = db.scalar(query)
    if not record or (user.role != "ADMIN" and record.user_id != user.id):
        raise HTTPException(404, "기록을 찾을 수 없습니다.")
    if record.status == "DELETED":
        raise HTTPException(410, "삭제된 기록입니다.")
    return record


def ensure_idle(record):
    if record.status == "PENDING":
        raise HTTPException(409, "분석 중에는 변경할 수 없습니다.")


def serialize(db, record, detail=False):
    result = db.get(AnalysisResult, record.current_analysis_id) if record.current_analysis_id else None
    value = fields(record, {"file_path", "stored_filename"})
    value["analysis"] = (
        fields(result, () if detail else {"features_json", "provenance_json"}) if result else None
    )
    value["notice"] = NOTICE
    if detail:
        value["reviews"] = [
            fields(r)
            for r in db.scalars(
                select(Review).where(Review.noise_record_id == record.id).order_by(Review.created_at.desc())
            )
        ]
        value["analysis_history"] = [
            fields(a, {"features_json"})
            for a in db.scalars(
                select(AnalysisResult)
                .where(AnalysisResult.noise_record_id == record.id)
                .order_by(AnalysisResult.created_at.desc())
            )
        ]
    return value


@router.post("/noise-records", status_code=202)
def upload(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    occurred_at: str = Form(...),
    description: str = Form(""),
    address: str = Form(""),
    public_consent: bool = Form(False),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    try:
        meta = UploadMetadata(
            title=title,
            latitude=latitude,
            longitude=longitude,
            occurred_at=occurred_at,
            description=description,
            address=address,
            public_consent=public_consent,
        )
        suffix = validate_header(file.filename, file.content_type)
    except (ValidationError, AudioError) as exc:
        raise HTTPException(422, str(exc))
    runner = request.app.state.runner
    if not runner.reserve():
        raise HTTPException(503, "분석 대기열이 가득 찼습니다. 잠시 후 다시 시도하세요.")
    stored = uid() + suffix
    path = storage_path(stored)
    path.parent.mkdir(parents=True, exist_ok=True)
    submitted = False
    try:
        size = 0
        with path.open("xb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_mb * 1024 * 1024:
                    raise HTTPException(413, "최대 업로드 크기를 초과했습니다.")
                out.write(chunk)
        if not size:
            raise HTTPException(422, "빈 파일입니다.")
        waveform = decode(path)
        record = NoiseRecord(
            user_id=user.id,
            **meta.model_dump(),
            public_latitude=round(meta.latitude, 2),
            public_longitude=round(meta.longitude, 2),
            original_filename=file.filename[:255],
            stored_filename=stored,
            file_path=str(path),
            mime_type=file.content_type,
            file_size=size,
            duration=len(waveform) / settings.sample_rate,
        )
        db.add(record)
        db.flush()
        job = Job(noise_record_id=record.id, events_json=[{"stage": "UPLOADED", "at": now().isoformat()}])
        db.add(job)
        db.flush()
        record.current_job_id = job.id
        db.commit()
        runner.submit(job.id, waveform)
        submitted = True
        return {"id": record.id, "job_id": job.id, "status": "PENDING", "notice": NOTICE}
    except AudioError as exc:
        raise HTTPException(422, str(exc))
    finally:
        file.file.close()
        if not submitted:
            runner.slots.release()
            path.unlink(missing_ok=True)
            db.rollback()


def filters(
    query, *, start=None, end=None, noise_type=None, status=None, region=None, user_id=None, search=None
):
    if start:
        query = query.where(NoiseRecord.occurred_at >= start)
    if end:
        query = query.where(NoiseRecord.occurred_at <= end)
    if noise_type:
        query = query.where(
            func.coalesce(NoiseRecord.confirmed_class, AnalysisResult.predicted_class) == noise_type
        )
    if status:
        query = query.where(NoiseRecord.status == status)
    if region:
        query = query.where(NoiseRecord.address.ilike(f"%{region}%"))
    if user_id:
        query = query.where(NoiseRecord.user_id == user_id)
    if search:
        query = query.where(
            or_(NoiseRecord.title.ilike(f"%{search}%"), NoiseRecord.address.ilike(f"%{search}%"))
        )
    return query


def filter_params(
    start: datetime | None = None,
    end: datetime | None = None,
    noise_type: str | None = Query(None, max_length=80),
    status: str | None = None,
    region: str | None = Query(None, max_length=300),
    user_id: str | None = None,
    search: str | None = Query(None, max_length=160),
):
    if start and end and start > end:
        raise HTTPException(422, "시작일은 종료일보다 빨라야 합니다.")
    return dict(
        start=start,
        end=end,
        noise_type=noise_type,
        status=status,
        region=region,
        user_id=user_id,
        search=search,
    )


def base_query(user):
    query = select(NoiseRecord).outerjoin(
        AnalysisResult, NoiseRecord.current_analysis_id == AnalysisResult.id
    )
    query = query.where(NoiseRecord.status != "DELETED")
    return query if user.role == "ADMIN" else query.where(NoiseRecord.user_id == user.id)


@router.get("/noise-records")
def records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = "newest",
    params=Depends(filter_params),
    user=Depends(current_user),
    db=Depends(get_db),
):
    query = filters(base_query(user), **params)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    order = {
        "newest": NoiseRecord.created_at.desc(),
        "oldest": NoiseRecord.created_at.asc(),
        "occurred": NoiseRecord.occurred_at.desc(),
    }.get(sort)
    if order is None:
        raise HTTPException(422, "정렬은 newest, oldest, occurred 중 선택하세요.")
    rows = db.scalars(
        query.order_by(order, NoiseRecord.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": [serialize(db, r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/admin/noise-records", dependencies=[Depends(admin)])
def admin_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = "newest",
    params=Depends(filter_params),
    user=Depends(admin),
    db=Depends(get_db),
):
    return records(page, page_size, sort, params, user, db)


@router.get("/noise-records/{record_id}")
def detail(record_id: str, user=Depends(current_user), db=Depends(get_db)):
    return serialize(db, owned(db, record_id, user), True)


@router.get("/noise-records/{record_id}/analysis")
def analysis(record_id: str, user=Depends(current_user), db=Depends(get_db)):
    return serialize(db, owned(db, record_id, user), True)["analysis"]


@router.get("/noise-records/{record_id}/audio")
def download(record_id: str, user=Depends(current_user), db=Depends(get_db)):
    record = owned(db, record_id, user)
    path = storage_path(record.stored_filename)
    if record.original_deleted_at or not path.is_file():
        raise HTTPException(410, "원본 음성이 삭제되었습니다.")
    return FileResponse(
        path,
        media_type=record.mime_type,
        filename="soundwatch" + path.suffix,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/noise-records/{record_id}/audio")
def delete_audio(record_id: str, request: Request, user=Depends(current_user), db=Depends(get_db)):
    record = owned(db, record_id, user, True)
    ensure_idle(record)
    if record.original_deleted_at:
        raise HTTPException(410, "이미 삭제된 원본입니다.")
    remove_original(record)
    remove_reconstructable_features(db, record)
    if not record.public_consent:
        purge_record(db, record)
    audit(
        db,
        user,
        "DELETE_AUDIO",
        record.id,
        {"audio_present": True},
        {"audio_present": False, "status": record.status},
        "원본 삭제 요청",
        request,
    )
    db.commit()
    return {
        "status": record.status,
        "message": "원본 삭제 완료. 비동의 기록은 분석 특징과 메타데이터도 삭제됩니다.",
    }


@router.delete("/noise-records/{record_id}")
def delete_record(
    record_id: str, request: Request, body: Reason, user=Depends(current_user), db=Depends(get_db)
):
    record = owned(db, record_id, user, True)
    ensure_idle(record)
    before = {"status": record.status}
    if user.role == "ADMIN":
        purge_record(db, record)
        action = "DELETE_RECORD"
    else:
        record.deletion_requested_at = now()
        # Withdraw consent immediately while awaiting administrative deletion.
        record.public_consent = False
        action = "REQUEST_DELETION"
    audit(
        db,
        user,
        action,
        record.id,
        before,
        {"status": record.status, "requested": True},
        body.reason,
        request,
    )
    db.commit()
    return {"status": record.status, "deletion_requested": True}


@router.post("/noise-records/{record_id}/reanalyze", status_code=202)
def reanalyze(record_id: str, request: Request, body: Reason, user=Depends(admin), db=Depends(get_db)):
    record = owned(db, record_id, user, True)
    if record.status != "FAILED":
        raise HTTPException(409, "실패한 기록만 재분석할 수 있습니다.")
    if record.original_deleted_at:
        raise HTTPException(410, "원본이 삭제되어 재분석할 수 없습니다.")
    try:
        waveform = decode(storage_path(record.stored_filename))
    except AudioError as exc:
        raise HTTPException(422, str(exc))
    runner = request.app.state.runner
    if not runner.reserve():
        raise HTTPException(503, "분석 대기열이 가득 찼습니다.")
    try:
        job = Job(noise_record_id=record.id, events_json=[{"stage": "UPLOADED", "at": now().isoformat()}])
        db.add(job)
        db.flush()
        record.current_job_id, record.status = job.id, "PENDING"
        audit(
            db,
            user,
            "REANALYZE",
            record.id,
            {"status": "FAILED"},
            {"status": "PENDING"},
            body.reason,
            request,
        )
        db.commit()
        runner.submit(job.id, waveform)
    except Exception:
        runner.slots.release()
        raise
    return {"job_id": job.id, "id": record.id}


@router.get("/analysis/jobs/{job_id}")
def job_status(job_id: str, user=Depends(current_user), db=Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "작업을 찾을 수 없습니다.")
    owned(db, job.noise_record_id, user)
    return fields(job)


@router.websocket("/ws/analysis/{job_id}")
async def job_socket(websocket: WebSocket, job_id: str):
    # Authenticate in the first frame; never put JWTs in access-logged URLs.
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5)
        token = message.get("token", "")
        while True:
            with SessionLocal() as db:
                user = user_from_token(token, db)
                value = job_status(job_id, user, db)
            await websocket.send_json(
                __import__("fastapi.encoders", fromlist=["jsonable_encoder"]).jsonable_encoder(value)
            )
            if value["stage"] in {"COMPLETED", "FAILED"}:
                await websocket.close()
                return
            await asyncio.sleep(0.5)
    except Exception:
        try:
            await websocket.close(code=1008)
        except RuntimeError:
            pass


@router.post("/admin/noise-records/{record_id}/review")
def review(record_id: str, body: ReviewInput, request: Request, user=Depends(admin), db=Depends(get_db)):
    record = owned(db, record_id, user, True)
    ensure_idle(record)
    if record.status == "FAILED" or not record.current_analysis_id:
        raise HTTPException(409, "성공한 분석 결과가 있어야 검토할 수 있습니다.")
    if body.confirmed_class not in CLASSES:
        raise HTTPException(422, "지원하지 않는 소음 유형입니다.")
    result = db.get(AnalysisResult, record.current_analysis_id)
    previous = record.confirmed_class or result.predicted_class
    before = {"class": previous, "status": record.status}
    record.confirmed_class = body.confirmed_class
    record.status = (
        "REVIEW_REQUIRED"
        if body.status == "REVIEW_REQUIRED"
        else "CONFIRMED"
        if body.confirmed_class == result.predicted_class
        else "CORRECTED"
    )
    db.add(
        Review(
            noise_record_id=record.id,
            reviewer_id=user.id,
            previous_class=previous,
            confirmed_class=body.confirmed_class,
            comment=body.comment,
        )
    )
    audit(
        db,
        user,
        "REVIEW",
        record.id,
        before,
        {"class": record.confirmed_class, "status": record.status},
        body.comment,
        request,
    )
    db.commit()
    return serialize(db, record, True)


@router.get("/admin/users")
def users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = "",
    user=Depends(admin),
    db=Depends(get_db),
):
    query = select(User).where(or_(User.email.ilike(f"%{search}%"), User.name.ilike(f"%{search}%")))
    return {
        "items": [
            public_user(u)
            for u in db.scalars(
                query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        ],
        "total": db.scalar(select(func.count()).select_from(query.subquery())),
    }


@router.patch("/admin/users/{user_id}")
def patch_user(user_id: str, body: UserPatch, request: Request, actor=Depends(admin), db=Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "사용자를 찾을 수 없습니다.")
    if actor.id == user_id and (body.role == "USER" or body.is_active is False):
        raise HTTPException(409, "자신의 관리자 권한 또는 계정을 비활성화할 수 없습니다.")
    before = {"role": user.role, "is_active": user.is_active}
    for key, value in body.model_dump(exclude={"reason"}, exclude_none=True).items():
        setattr(user, key, value)
    audit(
        db,
        actor,
        "UPDATE_USER",
        user_id,
        before,
        {"role": user.role, "is_active": user.is_active},
        body.reason,
        request,
        "user",
    )
    db.commit()
    return public_user(user)


@router.get("/admin/audit-logs")
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = "",
    user=Depends(admin),
    db=Depends(get_db),
):
    query = select(AuditLog).where(
        or_(AuditLog.action.ilike(f"%{search}%"), AuditLog.target_id.ilike(f"%{search}%"))
    )
    return {
        "items": [
            fields(a)
            for a in db.scalars(
                query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        ],
        "total": db.scalar(select(func.count()).select_from(query.subquery())),
    }


def dashboard_data(db, user, params):
    records = db.scalars(filters(base_query(user), **params)).all()
    pairs = [
        (r, db.get(AnalysisResult, r.current_analysis_id) if r.current_analysis_id else None) for r in records
    ]
    results = [a for _, a in pairs if a and a.predicted_class]
    reviewed = [(r, a) for r, a in pairs if r.status in {"CONFIRMED", "CORRECTED"} and a]
    jobs = (
        db.scalars(select(Job).where(Job.noise_record_id.in_([r.id for r in records]))).all()
        if records
        else []
    )
    finished = [j for j in jobs if j.stage in {"COMPLETED", "FAILED"}]

    def avg(values):
        return sum(values) / len(values) if values else None

    def counter(values):
        return [{"name": k, "count": v} for k, v in sorted(Counter(values).items())]

    return {
        "total": len(records),
        "today": sum(r.created_at.date() == now().date() for r in records),
        "review_required": sum(r.status == "REVIEW_REQUIRED" for r in records),
        "failed": sum(r.status == "FAILED" for r in records),
        "average_inference_ms": avg([a.inference_time_ms for a in results]),
        "average_dbfs": avg([a.average_dbfs for a in results]),
        "maximum_dbfs": max([a.maximum_dbfs for a in results], default=None),
        "agreement_rate": avg([float(r.confirmed_class == a.predicted_class) for r, a in reviewed]),
        "review_required_rate": avg([float(r.status == "REVIEW_REQUIRED") for r in records]),
        "upload_processing_success_rate": avg([float(j.stage == "COMPLETED") for j in finished]),
        "average_processing_ms": avg(
            [j.processing_time_ms for j in finished if j.processing_time_ms is not None]
        ),
        "categories": counter(
            r.confirmed_class or a.predicted_class for r, a in pairs if a and a.predicted_class
        ),
        "hourly": counter(str(r.occurred_at.hour).zfill(2) for r in records),
        "weekday": counter(str(r.occurred_at.weekday()) for r in records),
        "regions": counter(r.address or "미지정" for r in records),
        "timeseries": counter(r.occurred_at.date().isoformat() for r in records),
        "metrics": {
            "api_test_pass_rate": None,
            "macro_f1": None,
            "test_coverage": None,
            "note": "측정 전: 테스트 결과는 docs/test-report.md 참조. DEMO 점수는 분류 성능이 아닙니다.",
        },
        "timezone": "UTC",
        "scope": "all" if user.role == "ADMIN" else "own",
        "notice": NOTICE,
    }


@router.get("/dashboard/summary")
def summary(params=Depends(filter_params), user=Depends(current_user), db=Depends(get_db)):
    return dashboard_data(db, user, params)


@router.get("/dashboard/timeseries")
def timeseries(params=Depends(filter_params), user=Depends(current_user), db=Depends(get_db)):
    return dashboard_data(db, user, params)["timeseries"]


@router.get("/dashboard/categories")
def categories(params=Depends(filter_params), user=Depends(current_user), db=Depends(get_db)):
    return dashboard_data(db, user, params)["categories"]


@router.get("/map/noise-events")
def map_events(
    south: float = Query(-90, ge=-90, le=90),
    north: float = Query(90, ge=-90, le=90),
    west: float = Query(-180, ge=-180, le=180),
    east: float = Query(180, ge=-180, le=180),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    params=Depends(filter_params),
    user=Depends(current_user),
    db=Depends(get_db),
):
    if south > north or west > east:
        raise HTTPException(422, "지도 영역이 올바르지 않습니다.")
    is_admin = user.role == "ADMIN"
    query = select(NoiseRecord).outerjoin(
        AnalysisResult, NoiseRecord.current_analysis_id == AnalysisResult.id
    )
    query = query.where(NoiseRecord.status.notin_(["DELETED", "PENDING", "FAILED"]))
    if not is_admin:
        query = query.where(NoiseRecord.public_consent.is_(True), NoiseRecord.deletion_requested_at.is_(None))
        # Do not let private text or owner filters become a public membership oracle.
        params = {**params, "search": None, "region": None, "user_id": None}
    lat = NoiseRecord.latitude if is_admin else NoiseRecord.public_latitude
    lon = NoiseRecord.longitude if is_admin else NoiseRecord.public_longitude
    query = filters(query, **params).where(lat.between(south, north), lon.between(west, east))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    values = []
    for r in db.scalars(
        query.order_by(NoiseRecord.occurred_at.desc(), NoiseRecord.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ):
        a = db.get(AnalysisResult, r.current_analysis_id)
        values.append(
            {
                "id": r.id if is_admin else None,
                "latitude": r.latitude if is_admin else r.public_latitude,
                "longitude": r.longitude if is_admin else r.public_longitude,
                "date": r.occurred_at.date().isoformat(),
                "status": r.status,
                "class": r.confirmed_class or a.predicted_class,
                "average_dbfs": a.average_dbfs,
                "inference_mode": a.inference_mode,
            }
        )
    return {"items": values, "total": total, "page": page, "anonymized": not is_admin}


@router.get("/system/model-status")
def system_status(user=Depends(current_user)):
    return {
        **model_status(),
        "classes": CLASSES,
        "notice_legal": NOTICE,
        "max_upload_mb": settings.max_upload_mb,
        "max_duration_seconds": settings.max_duration_seconds,
        "original_retention_days": settings.original_retention_days,
        "result_retention_days": settings.result_retention_days,
    }
