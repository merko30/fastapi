from fastapi import HTTPException, Request

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
    db = next(get_db())
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    request.state.user_id = None
    request.state.roles = None

    if access_token:
        try:
            # try normal decode
            payload = decode_token(access_token)
            request.state.user_id = payload.get("sub")
            request.state.roles = payload.get("roles")
        except HTTPException as e:
            if e.detail == "Token expired" and refresh_token:
                try:
                    # try refresh token
                    refresh_payload = decode_token(refresh_token)
                    user_id = refresh_payload.get("sub")
                    user = db.query(User).filter(User.id == int(user_id)).first()
                    if user:
                        # create and set new access token
                        new_access_token = create_access_token(user)
                        request.state.user_id = user.id
                        request.state.roles = user.roles

                        # attach new cookie
                        request.state.new_access_token = new_access_token
                except Exception:
                    request.state.user_id = None
            else:
                request.state.user_id = None

    response = await call_next(request)

    # set refreshed access token if one was issued
    # if hasattr(request.state, "new_access_token"):
    #     response.set_cookie(
    #         key="access_token",
    #         value=request.state.new_access_token,
    #         httponly=True,
    #         secure=False,  # True in prod
    #         samesite="lax",
    #         max_age=15 * 60,
    #         path="/",
    #     )

    # db.close()
    return response
