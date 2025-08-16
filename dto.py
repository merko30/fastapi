from pydantic import BaseModel


class ErrorDTO(BaseModel):
    code: int
    message: str
    field: str | None = None
