"""Chat service for managing AI agent conversations."""
import json
import logging
from typing import AsyncGenerator
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.memory_fact import MemoryFact
from app.models.user import User
from app.lib.agent.harness import InvestmentAgent, extract_memory_facts

logger = logging.getLogger(__name__)

# Max messages to replay as context
MAX_CONTEXT_MESSAGES = 20


class ChatService:
    """Manages AI agent conversations and message persistence."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_or_create_conversation(self, conversation_id: int | None = None) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id:
            conv = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == self.user_id,
            ).first()
            if conv:
                return conv

        # Create new conversation
        conv = Conversation(user_id=self.user_id)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def save_user_message(self, conversation: Conversation, content: str, metadata: dict | None = None) -> Message:
        """Save a user message to the conversation."""
        msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=content,
            metadata_json=metadata,
        )
        self.db.add(msg)

        # Set conversation title from first message
        if not conversation.title:
            conversation.title = content[:100] + ("..." if len(content) > 100 else "")

        self.db.commit()
        self.db.refresh(msg)
        return msg

    def save_assistant_message(self, conversation: Conversation, content: str, metadata: dict | None = None) -> Message:
        """Save an assistant response to the conversation."""
        msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=content,
            metadata_json=metadata,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_conversation_messages(self, conversation_id: int, limit: int = MAX_CONTEXT_MESSAGES) -> list[dict]:
        """Get recent messages for a conversation in Anthropic API format."""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
        ).order_by(Message.created_at.desc()).limit(limit).all()

        # Reverse to chronological order
        messages = list(reversed(messages))

        # Convert to Anthropic message format
        api_messages = []
        for msg in messages:
            if msg.role in ("user", "assistant"):
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        return api_messages

    def list_conversations(self, limit: int = 50, offset: int = 0) -> list[Conversation]:
        """List user's conversations, most recent first."""
        return self.db.query(Conversation).filter(
            Conversation.user_id == self.user_id,
        ).order_by(Conversation.updated_at.desc()).limit(limit).offset(offset).all()

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and all its messages."""
        conv = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == self.user_id,
        ).first()
        if not conv:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    async def stream_chat(
        self,
        conversation: Conversation,
        user_content: str,
        component_context: dict | None = None,
        model: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream a full chat turn: save user msg, get AI response, save assistant msg.

        Yields SSE-compatible event dicts.
        """
        # Build user message content
        message_content = user_content
        message_metadata = None
        if component_context:
            message_content = f"{user_content}\n\n[Component Context: {json.dumps(component_context.get('data', {}))}]"
            message_metadata = {"component_context": component_context.get("data")}

        # Save user message
        self.save_user_message(conversation, user_content, message_metadata)

        # Get conversation history
        messages = self.get_conversation_messages(conversation.id)

        # Ensure last message is the user's current message with full context
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] = message_content

        # Create agent and stream response
        agent = InvestmentAgent(
            user_id=self.user_id,
            db=self.db,
            conversation_id=conversation.id,
            model=model,
        )

        full_response = ""
        usage_data = None

        async for event in agent.stream_response(messages):
            if event["type"] == "token":
                full_response += event["content"]
            elif event["type"] == "done":
                full_response = event.get("content", full_response)
                usage_data = event.get("usage")

            yield event

        # Save assistant response
        if full_response:
            self.save_assistant_message(
                conversation,
                full_response,
                metadata={"usage": usage_data} if usage_data else None,
            )

        # Extract memory facts in background (non-blocking)
        try:
            user = self.db.query(User).filter(User.id == self.user_id).first()
            if user and user.ai_memory_enabled and full_response:
                combined = f"User: {user_content}\nAssistant: {full_response}"
                facts = await extract_memory_facts(combined, self.user_id)
                for fact in facts:
                    memory = MemoryFact(
                        user_id=self.user_id,
                        conversation_id=conversation.id,
                        fact_type=fact.get("fact_type", "preference"),
                        content=fact.get("content", ""),
                    )
                    self.db.add(memory)
                self.db.commit()
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")

        # Yield final done event with conversation_id
        yield {"type": "done", "conversation_id": conversation.id}
