"""Chat routes for AI agent conversations."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.chat_service import ChatService
from app.services.action_executor import ActionExecutor

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic schemas
class SendMessageRequest(BaseModel):
    content: str
    conversation_id: Optional[int] = None
    component_context: Optional[dict] = None
    model: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: str


# Routes
@router.get("/conversations")
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's conversations."""
    service = ChatService(db, current_user.id)
    conversations = service.list_conversations(limit, offset)
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in conversations
    ]


@router.post("/conversations")
async def create_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conversation."""
    service = ChatService(db, current_user.id)
    conv = service.get_or_create_conversation()
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages for a conversation."""
    # Verify ownership
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
    ).order_by(Message.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "metadata": m.metadata_json,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation."""
    service = ChatService(db, current_user.id)
    if not service.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message and stream the AI response via SSE."""
    service = ChatService(db, current_user.id)
    conversation = service.get_or_create_conversation(request.conversation_id)

    async def event_stream():
        try:
            async for event in service.stream_chat(
                conversation,
                request.content,
                request.component_context,
                model=request.model,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/actions/{action_id}/confirm")
async def confirm_action(
    action_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm and execute a pending action."""
    executor = ActionExecutor(db, current_user.id)
    result = executor.execute(action_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/actions/{action_id}/reject")
async def reject_action(
    action_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reject a pending action."""
    executor = ActionExecutor(db, current_user.id)
    result = executor.reject(action_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/actions/pending")
async def get_pending_actions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List pending actions for the user."""
    executor = ActionExecutor(db, current_user.id)
    return executor.get_pending_actions()
