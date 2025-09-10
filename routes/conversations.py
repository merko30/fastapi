from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from database import get_db
from utils.middleware import require_user_id
from models import Conversation, Message
from dto import ErrorDTO

router = APIRouter(prefix="/conversations")


@router.get("/")
def get_conversations(
    db: Session = Depends(get_db), user_id: int = Depends(require_user_id)
):
    conversations = (
        db.query(Conversation)
        .options(selectinload(Conversation.user), selectinload(Conversation.recipient))
        .filter(
            or_(Conversation.user_id == user_id, Conversation.recipient_id == user_id)
        )
        .all()
    )

    return conversations


@router.get("/{id}")
def get_conversation(id: int, db: Session = Depends(get_db)):
    conversation = (
        db.query(Conversation)
        .options(
            selectinload(Conversation.user),
            selectinload(Conversation.recipient),
            selectinload(Conversation.messages),
        )
        .where((Conversation.id == id))
        .first()
    )

    if not conversation:
        return ErrorDTO(code=404, message="Conversation not found")

    return conversation
