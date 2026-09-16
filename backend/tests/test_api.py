import io
from datetime import timedelta

import numpy as np
import pytest
import soundfile as sf
from conftest import finish, upload
from sqlalchemy import select

from app.audio import AudioError, extract, validate_header
from app.core.config import settings
from app.db import SessionLocal
from app.ml import CLASSES, DemoPredictor
from app.models import NoiseRecord, User, now
from app.security import attempts
from app.services import retention_cleanup


def test_health_and_ready(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 200


def test_registration_login_jwt(client):
    body = {"email": "test@example.com", "name": "테스터", "password": "long-password-123"}
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    assert client.post("/api/v1/auth/register", json=body).status_code == 409
    login = client.post("/api/v1/auth/login", json=body)
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert client.get("/api/v1/auth/me", headers=headers).json()["role"] == "USER"
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={**body, "password": "wrong"}).status_code == 401


def test_role_access_and_disabled_token(client, accounts):
    for path in ["/admin/noise-records", "/admin/users", "/admin/audit-logs"]:
        assert client.get("/api/v1" + path, headers=accounts["owner"]).status_code == 403
    response = client.patch(
        "/api/v1/admin/users/" + accounts["owner_id"],
        headers=accounts["admin"],
        json={"is_active": False, "reason": "테스트 비활성화"},
    )
    assert response.status_code == 200
    assert client.get("/api/v1/auth/me", headers=accounts["owner"]).status_code == 401


@pytest.mark.parametrize(
    "filename,mime",
    [("a.exe", "audio/wav"), ("a.wav", "text/plain"), ("../a.wav", "audio/wav"), ("C:\\a.wav", "audio/wav")],
)
def test_header_rejection(filename, mime):
    with pytest.raises(AudioError):
        validate_header(filename, mime)


@pytest.mark.parametrize(
    "ext,mime",
    [
        ("wav", "audio/wav"),
        ("mp3", "audio/mpeg"),
        ("m4a", "audio/mp4"),
        ("flac", "audio/flac"),
        ("ogg", "audio/ogg"),
    ],
)
def test_supported_headers(ext, mime):
    assert validate_header("sample." + ext, mime) == "." + ext


@pytest.mark.parametrize("content", [b"", b"not-an-audio-file"])
def test_empty_and_corrupt_rejected(client, accounts, content):
    assert upload(client, accounts["owner"], content).status_code == 422


def test_size_and_duration_limits(client, accounts, wav, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    assert upload(client, accounts["owner"], b"x" * (1024 * 1024 + 1)).status_code == 413
    monkeypatch.setattr(settings, "max_duration_seconds", 1)
    assert upload(client, accounts["owner"], wav).status_code == 422


def test_features_and_reproducibility():
    y = (0.5 * np.sin(2 * np.pi * 440 * np.arange(16000) / 16000)).astype(np.float32)
    features = extract(y, 16000)
    assert features["rms"] == pytest.approx(0.35355, abs=0.001)
    assert features["average_dbfs"] == pytest.approx(-9.0309, abs=0.01)
    assert features["maximum_dbfs"] == pytest.approx(-6.0206, abs=0.01)
    assert len(features["log_mel"]) == 64
    model = DemoPredictor()
    scores = model.predict(y, features)
    np.testing.assert_array_equal(scores, model.predict(y, extract(y, 16000)))
    assert scores.sum() == pytest.approx(1)
    silent = extract(np.zeros(16000, dtype=np.float32), 16000)
    assert silent["silence_ratio"] == 1 and silent["average_dbfs"] == -120
    assert not np.allclose(scores, model.predict(y, silent))


def test_upload_analysis_idor_map_statistics_and_review(client, accounts, wav):
    response = upload(client, accounts["owner"], wav)
    assert response.status_code == 202, response.text
    record_id, job_id = response.json()["id"], response.json()["job_id"]
    assert finish(client, accounts["owner"], job_id)["stage"] == "COMPLETED"
    path = "/api/v1/noise-records/" + record_id
    record = client.get(path, headers=accounts["owner"]).json()
    assert record["analysis"]["inference_mode"] == "DEMO"
    assert record["analysis"]["features_json"]["waveform"]
    assert record["status"] == "REVIEW_REQUIRED"
    assert "file_path" not in record and "stored_filename" not in record
    assert client.get(path, headers=accounts["other"]).status_code == 404
    assert client.get(path + "/audio", headers=accounts["other"]).status_code == 404
    assert client.get("/api/v1/noise-records", headers=accounts["other"]).json()["total"] == 0
    public = client.get("/api/v1/map/noise-events", headers=accounts["other"]).json()["items"][0]
    assert public["latitude"] == 37.57 and public["id"] is None
    assert "address" not in public and "title" not in public and "user_id" not in public
    original = client.get("/api/v1/map/noise-events", headers=accounts["admin"]).json()["items"][0]
    assert original["latitude"] == 37.566512
    stats = client.get("/api/v1/dashboard/summary", headers=accounts["owner"]).json()
    assert stats["total"] == 1 and stats["upload_processing_success_rate"] == 1
    assert stats["metrics"]["macro_f1"] is None
    new_class = next(c for c in CLASSES if c != record["analysis"]["predicted_class"])
    reviewed = client.post(
        f"/api/v1/admin/noise-records/{record_id}/review",
        headers=accounts["admin"],
        json={"confirmed_class": new_class, "comment": "합성 파형 검토 테스트"},
    )
    assert reviewed.status_code == 200 and reviewed.json()["status"] == "CORRECTED"
    assert reviewed.json()["reviews"][0]["previous_class"] == record["analysis"]["predicted_class"]
    logs = client.get("/api/v1/admin/audit-logs", headers=accounts["admin"]).json()["items"]
    assert logs[0]["action"] == "REVIEW" and logs[0]["request_id"]
    assert client.delete(path + "/audio", headers=accounts["owner"]).status_code == 200
    assert client.get(path + "/audio", headers=accounts["owner"]).status_code == 410
    assert client.get(path, headers=accounts["owner"]).json()["analysis"] is not None


def test_failure_reanalysis_and_websocket(client, accounts, wav, monkeypatch):
    monkeypatch.setattr(settings, "inference_mode", "MODEL")
    response = upload(client, accounts["owner"], wav).json()
    assert finish(client, accounts["owner"], response["job_id"])["stage"] == "FAILED"
    assert client.get("/health").status_code == 200
    assert not client.get("/api/v1/system/model-status", headers=accounts["admin"]).json()["ready"]
    monkeypatch.setattr(settings, "inference_mode", "DEMO")
    retried = client.post(
        f"/api/v1/noise-records/{response['id']}/reanalyze",
        headers=accounts["admin"],
        json={"reason": "DEMO 설정 복원 후 재시도"},
    )
    assert retried.status_code == 202
    job_id = retried.json()["job_id"]
    finish(client, accounts["owner"], job_id)
    with client.websocket_connect("/api/v1/ws/analysis/" + job_id) as ws:
        ws.send_json({"token": accounts["owner"]["Authorization"].split()[1]})
        payload = ws.receive_json()
        assert payload["stage"] == "COMPLETED"
        assert {e["stage"] for e in payload["events_json"]} >= {
            "VALIDATING",
            "PREPROCESSING",
            "INFERENCING",
            "SAVING",
        }
    record = client.get("/api/v1/noise-records/" + response["id"], headers=accounts["owner"]).json()
    assert len(record["analysis_history"]) == 2


def test_nonconsent_deletion_and_rollback(client, accounts, wav):
    response = upload(client, accounts["owner"], wav, False).json()
    finish(client, accounts["owner"], response["job_id"])
    assert client.get("/api/v1/map/noise-events", headers=accounts["other"]).json()["total"] == 0
    path = "/api/v1/noise-records/" + response["id"]
    assert client.delete(path + "/audio", headers=accounts["owner"]).json()["status"] == "DELETED"
    assert client.get(path, headers=accounts["owner"]).status_code == 410
    with SessionLocal() as db:
        user = db.get(User, accounts["owner_id"])
        user.name = "must rollback"
        db.flush()
        db.rollback()
    with SessionLocal() as db:
        assert db.get(User, accounts["owner_id"]).name == "owner"


def test_deletion_request_and_retention(client, accounts, wav):
    response = upload(client, accounts["owner"], wav).json()
    finish(client, accounts["owner"], response["job_id"])
    path = "/api/v1/noise-records/" + response["id"]
    assert (
        client.request(
            "DELETE", path, headers=accounts["owner"], json={"reason": "기록 삭제 요청"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/map/noise-events", headers=accounts["other"]).json()["total"] == 0
    with SessionLocal() as db:
        record = db.get(NoiseRecord, response["id"])
        record.created_at = now() - timedelta(days=100)
        db.commit()
    retention_cleanup()
    assert client.get(path, headers=accounts["owner"]).status_code == 410


def test_invalid_coordinates_and_time(client, accounts, wav):
    response = client.post(
        "/api/v1/noise-records",
        headers=accounts["owner"],
        data={"title": "test", "latitude": 999, "longitude": 1, "occurred_at": "2026-01-01"},
        files={"file": ("test.wav", wav, "audio/wav")},
    )
    assert response.status_code == 422


def test_login_throttling(client):
    attempts.clear()
    for _ in range(10):
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "no@example.com", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post("/api/v1/auth/login", json={"email": "no@example.com", "password": "wrong"}).status_code
        == 429
    )


def test_wav_stereo_decode(client, accounts):
    buffer = io.BytesIO()
    sf.write(buffer, np.zeros((16000, 2)), 16000, format="WAV")
    response = upload(client, accounts["owner"], buffer.getvalue()).json()
    assert finish(client, accounts["owner"], response["job_id"])["stage"] == "COMPLETED"
    with SessionLocal() as db:
        assert db.scalar(select(NoiseRecord)).duration == 1
