from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from utils.websocket.manager import manager
from utils.websocket.handlers import handler

from utils.middleware import add_user_to_request

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Environment variable DATABASE_URL is not set!")


from routes.plans import router as plans_router
from routes.users import router as auth_router
from routes.coaches import router as coaches_router
from routes.conversations import router as conversations_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.middleware("http")(add_user_to_request)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            obj = json.loads(data)
            await handler.handle(websocket, obj)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


app.include_router(plans_router)
app.include_router(auth_router)
app.include_router(coaches_router)
app.include_router(conversations_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
