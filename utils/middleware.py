from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from .jwt import decode_token, create_access_token
from models import User
from database import get_db

from dto import ErrorDTO


def require_user_id(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=ErrorDTO(code=401, message="Unauthorized").model_dump(),
        )
    return user_id


def require_coach(request: Request):
    access_token = request.cookies.get("access_token")

    payload = decode_token(access_token)

    if "coach" not in payload["roles"]:
        raise HTTPException(
            status_code=403,
            detail=ErrorDTO(code=403, message="Forbidden").model_dump(),
        )

    return True


async def add_user_to_request(request: Request, call_next):
    db: Session = next(get_db())
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    new_access_token = None

    if access_token:
        try:
            # Try normal decode
            payload = decode_token(access_token)
            request.state.user_id = payload.get("sub")
            request.state.roles = payload.get("roles")
        except HTTPException as e:
            # Token expired, try refresh
            if e.detail == "Token expired" and refresh_token:
                try:
                    refresh_payload = decode_token(refresh_token)
                    user_id = refresh_payload.get("sub")
                    user = db.query(User).filter(User.id == int(user_id)).first()
                    if user:
                        # Create new access token
                        new_access_token = create_access_token(user)
                        request.state.user_id = user.id
                        request.state.roles = user.roles
                except Exception:
                    request.state.user_id = None
            else:
                request.state.user_id = None
    else:
        request.state.user_id = None

    # Call next middleware / endpoint
    response = await call_next(request)

    # Attach new access token if generated
    if new_access_token:
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,  # optional: True in production
            samesite="lax",  # adjust as needed
            max_age=15 * 60,  # 15 minutes
        )

    db.close()
    return response
