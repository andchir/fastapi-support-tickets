from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


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
