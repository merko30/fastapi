from dotenv import load_dotenv
from fastapi import FastAPI, Request
import os

from utils.jwt import decode_token

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Environment variable DATABASE_URL is not set!")


from routes.plans import router as plans_router
from routes.users import router as auth_router

app = FastAPI()


@app.middleware("http")
async def add_user_id(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
            request.state.user_id = payload.get("sub")
        except Exception:
            request.state.user_id = None
    else:
        request.state.user_id = None

    response = await call_next(request)
    return response


app.include_router(plans_router)
app.include_router(auth_router)
