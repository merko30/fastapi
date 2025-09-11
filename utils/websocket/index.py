from fastapi import WebSocket


class WebSocketHandler:
    def __init__(self, db_session):
        self.db = db_session
        self.handlers = {}

    def register(self, message_type: str):
        def decorator(func):
            self.handlers[message_type] = func
            return func

        return decorator

    async def handle(self, websocket: WebSocket, data: dict):
        message_type = data.get("type")
        handler = self.handlers.get(message_type)
        if handler:
            await handler(websocket, data)
        else:
            print(f"No handler for type: {message_type}")
