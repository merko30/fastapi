from datetime import datetime, timedelta, timezone
import jwt

SECRET = "supersecret"


def create_access_token(user_id: int):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "exp": now + timedelta(minutes=15),
        "iat": now,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def create_refresh_token(user_id: int, jti: str):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": jti,  # unique ID for revocation
        "exp": now + timedelta(days=7),
        "iat": now,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")
