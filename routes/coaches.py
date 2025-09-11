from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, selectinload

from database import get_db
from dto import ErrorDTO
from models import Coach
from utils.middleware import require_user_id

router = APIRouter(prefix="/coaches")


@router.get("/")
def get_coaches(db: Session = Depends(get_db)):
    coaches = db.query(Coach).options(selectinload(Coach.plans)).all()

    return coaches


@router.get("/auth")
def get_coaches(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):

    coaches = (
        db.query(Coach)
        .options(selectinload(Coach.plans))
        .where(Coach.user_id == user_id)
        .first()
    )

    return coaches
