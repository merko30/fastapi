from dotenv import load_dotenv
from fastapi import FastAPI
import os

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Environment variable DATABASE_URL is not set!")


from routes.posts import router as posts_router
from routes.users import router as auth_router

app = FastAPI()

app.include_router(posts_router)
app.include_router(auth_router)
