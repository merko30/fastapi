from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import json

from utils.jwt import decode_token

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Environment variable DATABASE_URL is not set!")


from routes.plans import router as plans_router
from routes.users import router as auth_router
from routes.coaches import router as coaches_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_user_id(request: Request, call_next):
    token = request.cookies.get("access_token")
    try:
        payload = decode_token(token)
        print(payload)
        request.state.user_id = payload.get("sub")
        request.state.roles = payload.get("roles")
    except Exception:
        request.state.user_id = None

    response = await call_next(request)
    return response


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            obj = json.loads(data)  # parse JSON string into dict
            print("Received object:", obj)

            await manager.broadcast(
                {
                    "type": "chat",
                    "raw": obj,
                }
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


app.include_router(plans_router)
app.include_router(auth_router)
app.include_router(coaches_router)
