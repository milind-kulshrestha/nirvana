"""MemoryFact model for AI agent long-term memory."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class MemoryFact(Base):
    """MemoryFact model for storing learned facts about users."""

    __tablename__ = "memory_facts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    fact_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="memory_facts")
    conversation = relationship("Conversation", back_populates="memory_facts")

    def __repr__(self):
        return f"<MemoryFact(id={self.id}, user_id={self.user_id}, fact_type={self.fact_type})>"
