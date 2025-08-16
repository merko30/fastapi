from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Post

router = APIRouter(prefix="/posts")


@router.get("/")
def get_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()
