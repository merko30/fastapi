from sqlalchemy.orm import Session
from fastapi import WebSocket

from .index import WebSocketHandler
from .manager import manager
from database import get_db
from models.index import Message
from models.dtos import MessageRead


db: Session = next(get_db())
handler = WebSocketHandler(db)


@handler.register("message")
async def handle_message(websocket: WebSocket, data: dict):
    if "conversation_id" in data:
        message = Message(
            sender_id=data["sender_id"],
            conversation_id=data["conversation_id"],
            content=data["content"],
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        message_read = MessageRead.model_validate(message)
        await manager.broadcast(
            {"type": "new_message", **message_read.model_dump(mode="json")}
        )


@handler.register("typing")
async def handle_typing(websocket: WebSocket, data: dict):
    # Example for typing notifications
    await manager.broadcast(
        {
            "type": "typing",
            "user_id": data["user_id"],
            "conversation_id": data["conversation_id"],
        }
    )


@handler.register("not-typing")
async def handle_typing(websocket: WebSocket, data: dict):
    await manager.broadcast(
        {
            "type": "not-typing",
            "user_id": data["user_id"],
            "conversation_id": data["conversation_id"],
        }
    )
