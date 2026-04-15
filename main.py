from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.routers import tickets, comments, admin, messages, utils, owners
from app.config import settings
from app.i18n import get_language, translate_http_detail, translate_validation_errors


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
app.mount("/demo", StaticFiles(directory="static/demo", html=True), name="demo")
app.mount("/demo-admin", StaticFiles(directory="static/demo-admin", html=True), name="demo-admin")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    lang = get_language(request)
    translated = translate_validation_errors(exc.errors(), lang)
    return JSONResponse(status_code=422, content={"detail": translated})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    lang = get_language(request)
    detail = translate_http_detail(exc.detail, lang)
    headers = getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=headers)


app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(comments.router, prefix="/tickets", tags=["comments"])
app.include_router(admin.router, prefix="/admin/tickets", tags=["admin"])
app.include_router(owners.router, prefix="/admin/owners", tags=["owners"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(utils.router, prefix="/utils", tags=["utils"])


@app.get("/")
async def root():
    return {"message": "Support Tickets API"}
