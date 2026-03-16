from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.routers import tickets, comments, admin
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title="Support Tickets API",
    description="API для тикетов службы поддержки",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(comments.router, prefix="/tickets", tags=["comments"])
app.include_router(admin.router, prefix="/admin/tickets", tags=["admin"])


@app.get("/")
async def root():
    return {"message": "Support Tickets API"}
