"""WatchlistItem model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class WatchlistItem(Base):
    """WatchlistItem model for stocks in a watchlist."""

    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "symbol", name="unique_watchlist_symbol"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(
        Integer,
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol = Column(String(20), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")

    def __repr__(self):
        return f"<WatchlistItem(id={self.id}, symbol={self.symbol}, watchlist_id={self.watchlist_id})>"
