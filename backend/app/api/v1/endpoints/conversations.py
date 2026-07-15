import json
import time
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse

router = APIRouter()


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Conversation)
        .where(Conversation.organization_id == current_user.organization_id, Conversation.status != "deleted")
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = Conversation(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        agent_id=req.agent_id,
        title=req.title,
        conversation_type=req.conversation_type,
        started_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == current_user.organization_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == current_user.organization_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    req: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == current_user.organization_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    content_json = req.content_json or {}
    if req.image_urls:
        content_json["image_urls"] = req.image_urls

    user_msg = Message(
        conversation_id=conversation_id,
        sender_type="user",
        sender_id=current_user.id,
        content_text=req.content_text,
        content_json=content_json if content_json else None,
        message_type="image" if req.image_urls else req.message_type,
    )
    db.add(user_msg)
    conv.last_message_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user_msg)

    from app.services.chat_service import ChatService
    chat_service = ChatService(db, current_user, conv)

    async def event_stream():
        try:
            async for event in chat_service.stream_response(user_msg):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{conversation_id}/summarize")
async def summarize_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == current_user.organization_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"success": True, "message": "Summarization queued"}
