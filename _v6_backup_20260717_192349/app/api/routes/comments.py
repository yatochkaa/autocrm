# ruff: noqa: B008
"""app/api/routes/comments.py  — NEW FILE (Phase 2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.db.enums import UserRole
from app.db.models import Lead
from app.db.models.comment import Comment
from app.db.models.user import User
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate

router = APIRouter(prefix="/leads", tags=["comments"])


async def _lead_or_404(lead_id: int, session: AsyncSession, current_user: User) -> Lead:
    lead = (
        await session.execute(
            select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.comments))
        )
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


async def _comment_or_404(comment_id: int, session: AsyncSession) -> Comment:
    c = await session.get(Comment, comment_id)
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")
    return c


@router.get("/{lead_id}/comments", response_model=list[CommentOut])
async def list_comments(
    lead_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CommentOut]:
    lead = await _lead_or_404(lead_id, session, current_user)
    return sorted(lead.comments, key=lambda c: c.created_at)


@router.post(
    "/{lead_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    lead_id: int,
    data: CommentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    await _lead_or_404(lead_id, session, current_user)
    comment = Comment(lead_id=lead_id, author_id=current_user.id, text=data.text)
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


@router.patch("/{lead_id}/comments/{comment_id}", response_model=CommentOut)
async def edit_comment(
    lead_id: int,
    comment_id: int,
    data: CommentUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    await _lead_or_404(lead_id, session, current_user)
    comment = await _comment_or_404(comment_id, session)
    if comment.lead_id != lead_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    if current_user.role != UserRole.ADMIN and comment.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Cannot edit someone else's comment"
        )
    comment.text = data.text
    await session.commit()
    await session.refresh(comment)
    return comment


@router.delete(
    "/{lead_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_comment(
    lead_id: int,
    comment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    await _lead_or_404(lead_id, session, current_user)

    comment = await _comment_or_404(comment_id, session)

    if comment.lead_id != lead_id:
        raise HTTPException(status_code=404, detail="Comment not found")

    if current_user.role != UserRole.ADMIN and comment.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete someone else's comment",
        )

    await session.delete(comment)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
