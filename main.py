from fastapi import FastAPI

from routes.posts import router as posts_router
from routes.users import router as auth_router

app = FastAPI()

app.include_router(posts_router)
app.include_router(auth_router)
