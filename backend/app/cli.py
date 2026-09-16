import argparse
import getpass
import os
from datetime import timedelta

from sqlalchemy import select

from app.audio import decode, write_synthetic
from app.db import SessionLocal
from app.models import Job, NoiseRecord, User, now, uid
from app.schemas import Register
from app.security import password_hash
from app.services import process_job, retention_cleanup, storage_path


def main():
    parser = argparse.ArgumentParser(description="SOUNDWATCH local administration")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--role", choices=["ADMIN", "USER"], default="USER")
    seed = sub.add_parser("seed")
    seed.add_argument("--email", required=True)
    sub.add_parser("cleanup")
    args = parser.parse_args()
    if args.command == "cleanup":
        retention_cleanup()
        print("Retention cleanup completed")
        return
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email.lower()))
        if args.command == "create-user":
            if user:
                parser.error("Account exists; no changes made")
            password = os.getenv("SOUNDWATCH_USER_PASSWORD") or getpass.getpass("Password (12+ characters): ")
            body = Register(email=args.email, name=args.name, password=password)
            db.add(
                User(
                    email=str(body.email).lower(),
                    name=body.name,
                    role=args.role,
                    password_hash=password_hash.hash(body.password),
                )
            )
            db.commit()
            print("Account created")
        elif not user:
            parser.error("Create the owner account first")
        else:
            for i, (lat, lon, place) in enumerate(
                [
                    (37.5665, 126.978, "합성 시연 · 서울 시청 일대"),
                    (37.570, 126.983, "합성 시연 · 종로 일대"),
                    (37.555, 126.970, "합성 시연 · 서울역 일대"),
                    (37.527, 126.932, "합성 시연 · 여의도 일대"),
                    (37.511, 127.060, "합성 시연 · 삼성동 일대"),
                ]
            ):
                stored = uid() + ".wav"
                path = storage_path(stored)
                path.parent.mkdir(parents=True, exist_ok=True)
                write_synthetic(path, i)
                record = NoiseRecord(
                    user_id=user.id,
                    title=f"[합성 DEMO] 도시 소음 샘플 {i + 1}",
                    description="실제 환경 녹음이 아닌 수학적 합성 파형입니다.",
                    occurred_at=now() - timedelta(days=i, hours=i),
                    latitude=lat,
                    longitude=lon,
                    public_latitude=round(lat, 2),
                    public_longitude=round(lon, 2),
                    address=place,
                    public_consent=True,
                    original_filename="synthetic.wav",
                    stored_filename=stored,
                    file_path=str(path),
                    mime_type="audio/wav",
                    file_size=path.stat().st_size,
                )
                db.add(record)
                db.flush()
                job = Job(noise_record_id=record.id)
                db.add(job)
                db.flush()
                record.current_job_id = job.id
                db.commit()
                process_job(job.id, decode(path))
            print("Created 5 explicitly labeled synthetic DEMO records")


if __name__ == "__main__":
    main()
