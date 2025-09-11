from fastapi import HTTPException, Request

from .jwt import decode_token

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
