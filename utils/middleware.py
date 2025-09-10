from fastapi import HTTPException, Request

from dto import ErrorDTO


def require_user_id(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=ErrorDTO(code=401, message="Unauthorized").model_dump(),
        )
    return user_id
