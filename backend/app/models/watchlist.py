"""Watchlist model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Watchlist(Base):
    """Watchlist model for organizing stocks."""

    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship(
        "WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Watchlist(id={self.id}, name={self.name}, user_id={self.user_id})>"
