"""Custom ETF symbols added by the user."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.database import Base


class EtfCustomSymbol(Base):
    __tablename__ = "etf_custom_symbols"

    symbol    = Column(String(20), primary_key=True)
    added_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
