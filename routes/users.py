from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Request,
    File,
    UploadFile,
)
from sqlalchemy.orm import Session, selectinload
from bcrypt import hashpw, gensalt, checkpw
from database import get_db
from botocore.exceptions import NoCredentialsError
from uuid import uuid4

from utils.s3 import s3_client, BUCKET_NAME
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

    if user.avatar:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": user.avatar},
            ExpiresIn=3600,  # 1 hour
        )
        user.avatar = presigned_url

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


@router.post("/avatar")
async def upload_file(
    file: UploadFile | None = File(None),
    user_id: int = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    try:
        # Generate unique filename
        user = db.query(User).where(User.id == user_id).first()
        if not user:
            raise HTTPException(
                404, detail=ErrorDTO(code=404, message="User not found").model_dump()
            )
        file_key = None

        if file:
            file_key = f"users/{uuid4()}_{file.filename}"

            # Upload to S3
            s3_client.upload_fileobj(file.file, BUCKET_NAME, file_key)
        else:
            # No file → remove avatar
            if user.avatar:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=user.avatar)
            user.avatar = None

        user.avatar = file_key
        db.add(user)
        db.commit()
        db.refresh(user)

        return {"avatar": file_key}

    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
