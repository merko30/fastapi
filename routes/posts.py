from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Post, PostCreate
from utils.middleware import require_user_id

router = APIRouter(prefix="/posts")


@router.get("/")
def get_posts(db: Session = Depends(get_db)):
    return db.query(Post).options(selectinload(Post.author)).all()


@router.post("/")
def get_posts(
    data: PostCreate, db: Session = Depends(get_db), user_id=Depends(require_user_id)
):

    new_post = data.model_dump()
    new_post["user_id"] = user_id
    post = Post(**new_post)
    db.add(post)
    db.commit()
    db.refresh(post)

    return post
