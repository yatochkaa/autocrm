from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentBase(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    author_id: int | None = None
    text: str
    created_at: datetime
    updated_at: datetime


CommentOut = CommentRead
