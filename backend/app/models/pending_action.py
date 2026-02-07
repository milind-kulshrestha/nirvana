"""PendingAction model for AI agent actions awaiting user approval."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class PendingAction(Base):
    """PendingAction model for actions that require user confirmation."""

    __tablename__ = "pending_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type = Column(String(50), nullable=False)
    action_payload = Column(JSON, nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="pending_actions")
    conversation = relationship("Conversation", back_populates="pending_actions")

    def __repr__(self):
        return f"<PendingAction(id={self.id}, action_type={self.action_type}, status={self.status})>"
