from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Post, PostCreate
from utils.middleware import require_user_id
from dto import ErrorDTO

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


@router.get("/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post = (
        db.query(Post).filter(Post.id == id).options(selectinload(Post.author)).first()
    )

    if not post:
        raise HTTPException(
            404, detail=ErrorDTO(code=404, message="Post not found").model_dump()
        )

    return post
