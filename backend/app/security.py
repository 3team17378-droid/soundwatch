import time
from collections import defaultdict, deque
from datetime import timedelta
from threading import Lock

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import User, now

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash("timing-defense-not-an-account-password")
bearer = HTTPBearer(auto_error=False)
attempts = defaultdict(deque)
attempt_lock = Lock()


def throttle(request: Request):
    key = request.client.host if request.client else "unknown"
    stamp = time.monotonic()
    with attempt_lock:
        for old in list(attempts):
            while attempts[old] and attempts[old][0] < stamp - 60:
                attempts[old].popleft()
            if not attempts[old]:
                del attempts[old]
        if len(attempts[key]) >= 10:
            raise HTTPException(429, "시도가 너무 많습니다. 1분 후 다시 시도하세요.")
        attempts[key].append(stamp)


def token_for(user):
    return jwt.encode(
        {
            "sub": user.id,
            "exp": now() + timedelta(minutes=settings.access_token_minutes),
            "iat": now(),
            "iss": "soundwatch",
            "aud": "soundwatch-web",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer="soundwatch",
            audience="soundwatch-web",
            options={"require": ["exp", "sub", "iat"]},
        )
        user = db.get(User, payload["sub"])
        if not user or not user.is_active:
            raise ValueError()
        return user
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            401, "인증이 만료되었거나 유효하지 않습니다.", headers={"WWW-Authenticate": "Bearer"}
        )


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(401, "로그인이 필요합니다.")
    return user_from_token(credentials.credentials, db)


def admin(user: User = Depends(current_user)):
    if user.role != "ADMIN":
        raise HTTPException(403, "관리자 권한이 필요합니다.")
    return user


def public_user(user):
    return {
        k: getattr(user, k) for k in ["id", "email", "name", "role", "is_active", "created_at", "updated_at"]
    }
