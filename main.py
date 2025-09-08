from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os

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
        request.state.user_id = payload.get("sub")
        request.state.roles = payload.get("roles")
    except Exception:
        request.state.user_id = None

    response = await call_next(request)
    return response


app.include_router(plans_router)
app.include_router(auth_router)
app.include_router(coaches_router)
