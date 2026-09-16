import hashlib
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Protocol

from sqlalchemy import select

from app.audio import extract
from app.core.config import settings
from app.db import SessionLocal
from app.ml import CLASSES, get_predictor
from app.models import AnalysisResult, AuditLog, Job, NoiseRecord, now, uid

logger = logging.getLogger("soundwatch")


def fields(obj, exclude=()):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name not in exclude}


def audit(db, actor, action, target, before, after, reason, request=None, target_type="noise_record"):
    db.add(
        AuditLog(
            actor_id=actor.id if actor else None,
            action=action,
            target_type=target_type,
            target_id=target,
            before_json=before,
            after_json=after,
            reason=reason,
            request_id=getattr(request.state, "request_id", uid()) if request else uid(),
            ip_address=request.client.host if request and request.client else "system",
        )
    )


def storage_path(stored_filename):
    root = (settings.storage_dir / "originals").resolve()
    path = (root / stored_filename).resolve()
    if path.parent != root:
        raise ValueError("Invalid storage path")
    return path


def remove_original(record):
    storage_path(record.stored_filename).unlink(missing_ok=True)
    record.original_deleted_at = now()
    record.original_filename = "[삭제됨]"
    record.file_path = ""
    if record.public_consent:
        record.title = "[비식별 보존] 환경 소음 기록"
        record.description = record.address = ""
        record.latitude, record.longitude = record.public_latitude, record.public_longitude
        record.occurred_at = record.occurred_at.replace(hour=0, minute=0, second=0, microsecond=0)


def remove_reconstructable_features(db, record):
    for result in db.scalars(select(AnalysisResult).where(AnalysisResult.noise_record_id == record.id)):
        result.features_json = {
            k: v for k, v in result.features_json.items() if k not in {"waveform", "log_mel"}
        }


def purge_record(db, record):
    remove_original(record)
    record.status = "DELETED"
    record.title, record.description, record.address = "[삭제됨]", "", ""
    record.latitude = record.longitude = record.public_latitude = record.public_longitude = 0
    record.public_consent = False
    for result in db.scalars(select(AnalysisResult).where(AnalysisResult.noise_record_id == record.id)):
        db.delete(result)
    record.current_analysis_id = None


def retention_cleanup():
    with SessionLocal() as db:
        records = db.scalars(
            select(NoiseRecord).where(NoiseRecord.status.notin_(["PENDING", "DELETED"]))
        ).all()
        stamp = now().replace(tzinfo=None)
        for record in records:
            age = stamp - record.created_at.replace(tzinfo=None)
            if age > timedelta(days=settings.result_retention_days):
                purge_record(db, record)
                audit(db, None, "RETENTION_PURGE", record.id, {}, {"status": "DELETED"}, "분석 보존기간 만료")
            elif not record.original_deleted_at and age > timedelta(days=settings.original_retention_days):
                remove_original(record)
                remove_reconstructable_features(db, record)
                if not record.public_consent:
                    purge_record(db, record)
                audit(
                    db, None, "RETENTION_AUDIO", record.id, {}, {"audio_deleted": True}, "원본 보존기간 만료"
                )
        db.commit()


class JobRunner(Protocol):
    def submit(self, job_id: str, waveform): ...


def process_job(job_id, waveform):
    started = time.perf_counter()
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        record = db.get(NoiseRecord, job.noise_record_id)

        def stage(name, progress):
            job.stage, job.progress = name, progress
            job.events_json = [*job.events_json, {"stage": name, "at": now().isoformat()}]
            db.commit()

        model = None
        try:
            stage("VALIDATING", 15)
            stage("PREPROCESSING", 35)
            features = extract(waveform, settings.sample_rate)
            stage("INFERENCING", 60)
            start_inference = time.perf_counter()
            model = get_predictor()
            scores = model.predict(waveform, features)
            inference_ms = (time.perf_counter() - start_inference) * 1000
            order = scores.argsort()[::-1][:3]
            predictions = [{"class": CLASSES[i], "probability": float(scores[i])} for i in order]
            stage("SAVING", 85)
            result = AnalysisResult(
                noise_record_id=record.id,
                predicted_class=predictions[0]["class"],
                confidence=predictions[0]["probability"],
                top_predictions_json=predictions,
                model_name=model.name,
                model_version=model.version,
                inference_mode=model.mode,
                inference_time_ms=inference_ms,
                low_confidence=predictions[0]["probability"] < settings.confidence_threshold,
                features_json=features,
                provenance_json={
                    "audio_sha256": hashlib.sha256(waveform.tobytes()).hexdigest(),
                    "model_sha256": getattr(model, "sha256", None),
                    "threshold": settings.confidence_threshold,
                    "segment_samples": 160000,
                    "sample_rate": settings.sample_rate,
                },
                **{
                    k: features[k]
                    for k in ["rms", "peak_amplitude", "average_dbfs", "maximum_dbfs", "silence_ratio"]
                },
            )
            db.add(result)
            db.flush()
            record.current_analysis_id = result.id
            record.duration = features["duration"]
            record.status = "REVIEW_REQUIRED" if result.low_confidence else "ANALYZED"
            job.processing_time_ms = (time.perf_counter() - started) * 1000
            stage("COMPLETED", 100)
        except Exception:
            db.rollback()
            record = db.get(NoiseRecord, job.noise_record_id)
            job = db.get(Job, job_id)
            message = "분석에 실패했습니다. 모델 설정과 파일 상태를 확인한 뒤 재분석하세요."
            failed = AnalysisResult(
                noise_record_id=record.id,
                model_name=getattr(model, "name", settings.model_name),
                model_version=getattr(model, "version", settings.model_version),
                inference_mode=settings.inference_mode,
                error_message=message,
            )
            db.add(failed)
            db.flush()
            record.current_analysis_id, record.status = failed.id, "FAILED"
            job.error = message
            job.processing_time_ms = (time.perf_counter() - started) * 1000
            stage("FAILED", 100)
            logger.error("analysis_failed", extra={"job_id": job_id})


class LocalJobRunner:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analysis")
        self.slots = threading.BoundedSemaphore(8)

    def reserve(self):
        return self.slots.acquire(blocking=False)

    def submit(self, job_id, waveform):
        future = self.executor.submit(process_job, job_id, waveform)
        future.add_done_callback(lambda _: self.slots.release())

    def shutdown(self):
        self.executor.shutdown(wait=True)
