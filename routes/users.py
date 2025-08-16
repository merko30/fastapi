from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from bcrypt import hashpw, gensalt

from database import get_db
from models import User, UserCreate
from dto import ErrorDTO

router = APIRouter(prefix="/auth")


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(
            400,
            detail=ErrorDTO(code=400, message="User already exists").model_dump(),
        )

    user_data = user.model_dump()
    password = hashpw(user.password.encode("utf-8"), gensalt())
    user_data["password"] = password.decode("utf-8")
    new_user = User(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
