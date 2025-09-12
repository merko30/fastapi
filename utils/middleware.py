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


async def add_user_to_request(request: Request, call_next):
    access_token = request.cookies.get("access_token")
    # refresh_token = request.cookies.get("refresh_token")

    if access_token:
        try:
            # Try normal decode
            payload = decode_token(access_token)
            request.state.user_id = payload.get("sub")
            request.state.roles = payload.get("roles")
        except HTTPException as e:
            request.state.user_id = None
    else:
        request.state.user_id = None

    # Call next middleware / endpoint
    response = await call_next(request)

    return response
