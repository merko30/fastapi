from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Coach

router = APIRouter(prefix="/coaches")


@router.get("/")
def get_coaches(db: Session = Depends(get_db)):
    coaches = db.query(Coach).options(selectinload(Coach.plans)).all()

    return coaches
