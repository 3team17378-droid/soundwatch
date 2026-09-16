import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid.uuid4())


class Stamp:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class User(Stamp, Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(10), default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class NoiseRecord(Stamp, Base):
    __tablename__ = "noise_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    public_latitude: Mapped[float] = mapped_column(Float)
    public_longitude: Mapped[float] = mapped_column(Float)
    address: Mapped[str] = mapped_column(String(300), default="")
    public_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(80))
    file_path: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    duration: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    confirmed_class: Mapped[str | None] = mapped_column(String(80))
    original_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_analysis_id: Mapped[str | None] = mapped_column(String(36))
    current_job_id: Mapped[str | None] = mapped_column(String(36))


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    noise_record_id: Mapped[str] = mapped_column(ForeignKey("noise_records.id"), index=True)
    predicted_class: Mapped[str | None] = mapped_column(String(80))
    confidence: Mapped[float | None] = mapped_column(Float)
    top_predictions_json: Mapped[list] = mapped_column(JSON, default=list)
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(100))
    inference_mode: Mapped[str] = mapped_column(String(10))
    inference_time_ms: Mapped[float | None] = mapped_column(Float)
    rms: Mapped[float | None] = mapped_column(Float)
    peak_amplitude: Mapped[float | None] = mapped_column(Float)
    average_dbfs: Mapped[float | None] = mapped_column(Float)
    maximum_dbfs: Mapped[float | None] = mapped_column(Float)
    silence_ratio: Mapped[float | None] = mapped_column(Float)
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    features_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Job(Stamp, Base):
    __tablename__ = "analysis_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    noise_record_id: Mapped[str] = mapped_column(ForeignKey("noise_records.id"), index=True)
    stage: Mapped[str] = mapped_column(String(40), default="UPLOADED")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    events_json: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text)
    processing_time_ms: Mapped[float | None] = mapped_column(Float)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    noise_record_id: Mapped[str] = mapped_column(ForeignKey("noise_records.id"))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    previous_class: Mapped[str | None] = mapped_column(String(80))
    confirmed_class: Mapped[str] = mapped_column(String(80))
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    before_json: Mapped[dict] = mapped_column(JSON, default=dict)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text)
    request_id: Mapped[str] = mapped_column(String(36))
    ip_address: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
