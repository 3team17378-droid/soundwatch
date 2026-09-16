import os
import tempfile
import time
from pathlib import Path

import pytest

test_root = Path(tempfile.mkdtemp(prefix="soundwatch-tests-"))
os.environ["JWT_SECRET"] = "test-only-" + "x" * 48
os.environ["DATABASE_URL"] = "sqlite:///" + (test_root / "test.db").as_posix()
os.environ["STORAGE_DIR"] = str(test_root / "storage")
os.environ["INFERENCE_MODE"] = "DEMO"

from fastapi.testclient import TestClient  # noqa: E402

from app.audio import write_synthetic  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import attempts, password_hash, token_for  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    attempts.clear()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def accounts(client):
    result = {}
    with SessionLocal() as db:
        for name, role in [("owner", "USER"), ("other", "USER"), ("admin", "ADMIN")]:
            user = User(
                email=f"{name}@example.com",
                name=name,
                role=role,
                password_hash=password_hash.hash("test-passphrase-123"),
            )
            db.add(user)
            db.flush()
            result[name] = {"Authorization": "Bearer " + token_for(user)}
            result[name + "_id"] = user.id
        db.commit()
    return result


@pytest.fixture
def wav(tmp_path):
    path = tmp_path / "synthetic.wav"
    write_synthetic(path)
    return path.read_bytes()


def upload(client, headers, wav, consent=True):
    return client.post(
        "/api/v1/noise-records",
        headers=headers,
        data={
            "title": "합성 시연",
            "latitude": "37.566512",
            "longitude": "126.978112",
            "occurred_at": "2026-09-14T10:00:00+09:00",
            "address": "비공개 상세주소",
            "description": "개인 설명",
            "public_consent": str(consent).lower(),
        },
        files={"file": ("synthetic.wav", wav, "audio/wav")},
    )


def finish(client, headers, job_id):
    for _ in range(300):
        response = client.get(f"/api/v1/analysis/jobs/{job_id}", headers=headers)
        data = response.json()
        if data.get("stage") in {"COMPLETED", "FAILED"}:
            return data
        time.sleep(0.1)
    pytest.fail("Analysis did not complete")
