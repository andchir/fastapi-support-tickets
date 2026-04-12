from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator

from app.config import settings


def _to_file_url(file_path: Optional[str]) -> Optional[str]:
    if not file_path:
        return file_path
    base = settings.base_url.rstrip("/")
    path = file_path.lstrip("/")
    return f"{base}/{path}"


class CommentCreate(BaseModel):
    author: str
    text: str


class CommentOut(BaseModel):
    id: int
    author: str
    text: str
    file_path: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def build_file_url(self):
        self.file_path = _to_file_url(self.file_path)
        return self


class TicketCreate(BaseModel):
    topic_uuid: str
    subject: str
    name: str
    email: str
    message: str


class TicketOut(BaseModel):
    id: int
    uuid: str
    topic_uuid: str
    subject: str
    name: str
    email: str
    message: str
    file_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def build_file_url(self):
        self.file_path = _to_file_url(self.file_path)
        return self


class TicketWithComments(TicketOut):
    comments: list[CommentOut] = []


class TicketStatusUpdate(BaseModel):
    status: str


class TicketListItem(BaseModel):
    id: int
    uuid: str
    topic_uuid: str
    subject: str
    name: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    items: list[TicketListItem]
    total: int
    page: int
    page_size: int


class MessageCreate(BaseModel):
    owner: str = Field(..., max_length=255)
    author: str = Field(..., max_length=255)
    text: str


class MessageOut(BaseModel):
    id: int
    owner: str
    author: str
    text: str
    created_at: datetime
    status: str

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageOut]
    total: int
    page: int
    page_size: int
