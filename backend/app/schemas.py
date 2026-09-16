from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Status = Literal["PENDING", "ANALYZED", "REVIEW_REQUIRED", "CONFIRMED", "CORRECTED", "FAILED", "DELETED"]


class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(min_length=1, max_length=80)


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UploadMetadata(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    address: str = Field(default="", max_length=300)
    occurred_at: datetime
    public_consent: bool = False

    @field_validator("occurred_at")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None:
            raise ValueError("발생 시각에 시간대가 필요합니다.")
        return value.astimezone(timezone.utc)

    @field_validator("title")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("제목을 입력하세요.")
        return value.strip()


class ReviewInput(BaseModel):
    confirmed_class: str
    comment: str = Field(min_length=3, max_length=2000)
    status: Literal["CONFIRMED", "CORRECTED", "REVIEW_REQUIRED"] = "CONFIRMED"


class UserPatch(BaseModel):
    role: Literal["USER", "ADMIN"] | None = None
    is_active: bool | None = None
    reason: str = Field(min_length=3, max_length=500)


class Reason(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
