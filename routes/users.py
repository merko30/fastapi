from fastapi import APIRouter, Depends, HTTPException, Response, Request
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
    UpdateData,
)
from dto import ErrorDTO
from utils.jwt import create_access_token, create_refresh_token, decode_token
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
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # localhost: http
        samesite="lax",  # allow cross-port on localhost
        max_age=15 * 60,
        path="/",
    )

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=CurrentUserRead)
def get_current_user(
    response: Response,
    user_id=Depends(require_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
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


@router.post("/refresh")
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # ✅ issue new access token
        new_access_token = create_access_token(user)

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=False,  # True in production
            samesite="lax",
            max_age=15 * 60,
            path="/",
        )

        return {"ok": True}

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.put("/me")
def update_current_user(
    data: UpdateData,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):

    user = db.query(User).where(User.id == user_id).first()
    coach = db.query(Coach).where(Coach.user_id == user_id).first()

    if not user:
        raise HTTPException(
            404, detail=ErrorDTO(code=404, message="User not found").model_dump()
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "description":
            coach.description = value
            db.add(coach)
        else:
            setattr(user, key, value)
            db.add(user)

    db.commit()
    return {"message": "User updated successfully"}
