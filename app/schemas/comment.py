"""Схемы комментария (create / read / update)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentBase(BaseModel):
    text: str = Field(min_length=1)


class CommentCreate(CommentBase):
    author_id: int | None = None


class CommentUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1)


class CommentRead(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    author_id: int | None
    created_at: datetime
