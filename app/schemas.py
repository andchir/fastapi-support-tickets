from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


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


class TicketCreate(BaseModel):
    subject: str
    name: str
    email: str
    message: str


class TicketOut(BaseModel):
    id: int
    uuid: str
    subject: str
    name: str
    email: str
    message: str
    file_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketWithComments(TicketOut):
    comments: list[CommentOut] = []


class TicketStatusUpdate(BaseModel):
    status: str


class TicketListItem(BaseModel):
    id: int
    uuid: str
    subject: str
    name: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
