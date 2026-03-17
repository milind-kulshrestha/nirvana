"""ETF dashboard routes."""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.models.etf_custom_symbol import EtfCustomSymbol
from app.lib.market_cache import get_etf_snapshot, get_etf_holdings, save_etf_holdings
from app.lib.etf_engine import stream_etf_refresh, fetch_etf_holdings_sync

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/snapshot")
async def snapshot(current_user: User = Depends(get_current_user)):
    """Return cached ETF snapshot or fallback if not yet built."""
    snapshot = get_etf_snapshot()
    if snapshot is None:
        return {"groups": {}, "built_at": None}
    return snapshot


@router.post("/refresh")
async def refresh(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SSE stream — fetches all ETFs and streams progress events."""
    custom_symbols = [row.symbol for row in db.query(EtfCustomSymbol).all()]

    async def event_stream():
        async for event in stream_etf_refresh(custom_symbols):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/holdings/{symbol}")
async def holdings(
    symbol: str,
    current_user: User = Depends(get_current_user),
):
    """Return ETF top-10 holdings (cached 24h, lazy-fetched on miss)."""
    cached = get_etf_holdings(symbol.upper())
    if cached is not None:
        return cached

    data = await asyncio.to_thread(fetch_etf_holdings_sync, symbol.upper())
    if data:
        save_etf_holdings(symbol.upper(), data)
    return data


@router.get("/custom")
async def get_custom(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return user's custom ETF symbols."""
    rows = db.query(EtfCustomSymbol).order_by(EtfCustomSymbol.added_at).all()
    return [row.symbol for row in rows]


@router.post("/custom/{symbol}", status_code=201)
async def add_custom(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a custom ETF symbol."""
    sym = symbol.upper()
    existing = db.query(EtfCustomSymbol).filter_by(symbol=sym).first()
    if existing:
        raise HTTPException(status_code=409, detail="Symbol already exists")
    db.add(EtfCustomSymbol(symbol=sym))
    db.commit()
    return {"symbol": sym, "status": "added"}


@router.delete("/custom/{symbol}")
async def remove_custom(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a custom ETF symbol."""
    sym = symbol.upper()
    row = db.query(EtfCustomSymbol).filter_by(symbol=sym).first()
    if not row:
        raise HTTPException(status_code=404, detail="Symbol not found")
    db.delete(row)
    db.commit()
    return {"symbol": sym, "status": "removed"}
