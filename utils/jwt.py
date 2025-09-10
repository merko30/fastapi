from typing import Any
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import jwt
from models import User

SECRET = "supersecret"
ALGORITHM = "HS256"


def create_access_token(user: User):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "roles": user.roles,
        "exp": now + timedelta(minutes=15),
        "iat": now,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def create_refresh_token(user_id: int):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        # "jti": jti,  # unique ID for revocation
        "exp": now + timedelta(days=7),
        "iat": now,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
