from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.routers import tickets, comments, admin, messages, utils
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

origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(comments.router, prefix="/tickets", tags=["comments"])
app.include_router(admin.router, prefix="/admin/tickets", tags=["admin"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(utils.router, prefix="/utils", tags=["utils"])


@app.get("/")
async def root():
    return {"message": "Support Tickets API"}
