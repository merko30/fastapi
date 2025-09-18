from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, selectinload

from database import get_db
from dto import ErrorDTO
from models.index import Coach
from models.dtos import CoachUpdateData
from utils.middleware import require_user_id, require_coach

router = APIRouter(prefix="/coaches")


@router.get("/")
def get_coaches(db: Session = Depends(get_db)):
    coaches = db.query(Coach).options(selectinload(Coach.plans)).all()

    return coaches


@router.get("/auth")
def get_coaches(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    is_coach: bool = Depends(require_coach),
):

    coaches = (
        db.query(Coach)
        .options(selectinload(Coach.plans))
        .where(Coach.user_id == user_id)
        .first()
    )

    return coaches


@router.put("/auth")
def update_coach(
    data: CoachUpdateData,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    is_coach: bool = Depends(require_coach),
):

    coach = db.query(Coach).where(Coach.user_id == user_id).first()

    if not coach:
        return ErrorDTO(message="Coach not found", status_code=404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(coach, key, value)
        db.add(coach)

    db.commit()

    return coach
