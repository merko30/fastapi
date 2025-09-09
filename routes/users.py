from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload
from bcrypt import hashpw, gensalt, checkpw

from database import get_db
from models import (
    User,
    UserCreate,
    LoginData,
    Coach,
    UserRead,
    Athlete,
    AthletePlan,
    Plan,
    CurrentUserRead,
)
from dto import ErrorDTO
from utils.jwt import create_access_token
from utils.middleware import require_user_id

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
    is_coach = user_data.pop("is_coach", False)
    password = hashpw(user.password.encode("utf-8"), gensalt())
    user_data["password"] = password.decode("utf-8")
    user_data["roles"] = ["coach"] if is_coach else ["athlete"]
    new_user = User(**user_data)

    db.add(new_user)
    db.flush()

    if is_coach:
        coach = Coach(user_id=new_user.id)
        db.add(coach)
    else:
        athlete = Athlete(user_id=new_user.id)
        db.add(athlete)

    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=UserRead)
def login(data: LoginData, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(
            401, detail=ErrorDTO(code=401, message="Invalid credentials").model_dump()
        )

    password_match = checkpw(
        data.password.encode("utf-8"), user.password.encode("utf-8")
    )

    if not password_match:
        raise HTTPException(
            401, detail=ErrorDTO(code=401, message="Invalid credentials").model_dump()
        )

    token = create_access_token(user)
    # refresh_token = create_refresh_token(user.id, "abc")

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # localhost: http
        samesite="lax",  # allow cross-port on localhost
        max_age=3600,
        path="/",
    )

    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


# @router.get("/me", response_model=UserRead)
# def get_current_user(
#     response: Response, user_id=Depends(require_user_id), db: Session = Depends(get_db)
# ):

#     user = db.query(User).filter(User.id == int(user_id)).first()

#     if not user:
#         response.delete_cookie("access_token")
#         raise HTTPException(
#             401, detail=ErrorDTO(code=401, message="Unauthorized").model_dump()
#         )

#     return user


@router.get("/me", response_model=CurrentUserRead)
def get_current_user(
    response: Response, user_id=Depends(require_user_id), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(user_id)).first()

    # TODO: move to middleware
    if not user:
        response.delete_cookie("access_token")
        raise HTTPException(
            401, detail=ErrorDTO(code=401, message="Unauthorized").model_dump()
        )

    athlete = db.query(Athlete).filter(Athlete.user_id == user.id).first()

    plans = []
    if athlete:
        athlete_plans = (
            db.query(AthletePlan)
            .filter(AthletePlan.athlete_id == athlete.id)
            .options(selectinload(AthletePlan.plan).selectinload(Plan.weeks))
            .all()
        )
        plans = [ap.plan for ap in athlete_plans]

    return {**user.__dict__, "plans": plans}
