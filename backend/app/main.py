import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text

from app.api import router
from app.core.config import settings
from app.db import SessionLocal, engine
from app.models import Job, NoiseRecord, uid
from app.services import LocalJobRunner, retention_cleanup


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "level": record.levelname,
                "event": record.getMessage(),
                "request_id": getattr(record, "request_id", None),
                "job_id": getattr(record, "job_id", None),
            },
            ensure_ascii=False,
        )


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("soundwatch")
logger.handlers = [handler]
logger.setLevel(logging.INFO)


async def cleanup_loop():
    while True:
        await asyncio.sleep(3600)
        try:
            await asyncio.to_thread(retention_cleanup)
        except Exception:
            logger.error("retention_cleanup_failed")


@asynccontextmanager
async def lifespan(app):
    with SessionLocal() as db:
        for job in db.scalars(select(Job).where(Job.stage.notin_(["COMPLETED", "FAILED"]))):
            job.stage, job.error = "FAILED", "서버 재시작으로 중단되었습니다. 관리자가 재분석할 수 있습니다."
            record = db.get(NoiseRecord, job.noise_record_id)
            if record and record.status == "PENDING":
                record.status = "FAILED"
        db.commit()
    retention_cleanup()
    app.state.runner = LocalJobRunner()
    cleanup_task = asyncio.create_task(cleanup_loop())
    yield
    cleanup_task.cancel()
    with suppress(asyncio.CancelledError):
        await cleanup_task
    app.state.runner.shutdown()


app = FastAPI(title="SOUNDWATCH", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        limit = (settings.max_upload_mb + 1) * 1024 * 1024
        try:
            declared = int(dict(scope["headers"]).get(b"content-length", b"0"))
        except ValueError:
            declared = limit + 1
        if declared > limit:
            return await JSONResponse({"detail": "요청 크기 제한을 초과했습니다."}, 413)(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > limit:
                return await JSONResponse({"detail": "요청 크기 제한을 초과했습니다."}, 413)(
                    scope, receive, send
                )
            chunks.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            return chunks.pop(0) if chunks else await receive()

        await self.app(scope, replay, send)


app.add_middleware(BodyLimit)


@app.middleware("http")
async def request_log(request, call_next):
    request.state.request_id = uid()
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    logger.info(
        "http_%s_%sms",
        response.status_code,
        round((time.perf_counter() - start) * 1000),
        extra={"request_id": request.state.request_id},
    )
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM users LIMIT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse({"status": "not_ready"}, 503)


app.include_router(router)
