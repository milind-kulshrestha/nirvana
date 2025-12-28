"""Watchlist routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.watchlist_item import WatchlistItem
from app.routes.auth import get_current_user
from app.lib.validators import validate_watchlist_name, validate_symbol

router = APIRouter()


# Pydantic schemas
class CreateWatchlistRequest(BaseModel):
    name: str


class WatchlistResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    items_count: int = 0


class AddItemRequest(BaseModel):
    symbol: str


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    added_at: datetime


@router.get("", response_model=list[WatchlistResponse])
async def list_watchlists(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get all watchlists for the current user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List of watchlists with item counts
    """
    # Query watchlists with item counts
    watchlists = (
        db.query(
            Watchlist.id,
            Watchlist.name,
            Watchlist.created_at,
            func.count(WatchlistItem.id).label("items_count"),
        )
        .outerjoin(WatchlistItem)
        .filter(Watchlist.user_id == current_user.id)
        .group_by(Watchlist.id)
        .all()
    )

    return [
        WatchlistResponse(
            id=w.id, name=w.name, created_at=w.created_at, items_count=w.items_count
        )
        for w in watchlists
    ]


@router.post("", response_model=WatchlistResponse, status_code=201)
async def create_watchlist(
    request: CreateWatchlistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new watchlist.

    Args:
        request: Watchlist creation request
        current_user: Authenticated user
        db: Database session

    Returns:
        Created watchlist

    Raises:
        HTTPException: If validation fails
    """
    # Validate name
    name = validate_watchlist_name(request.name)

    # Check watchlist limit (10 max)
    existing_count = (
        db.query(func.count(Watchlist.id))
        .filter(Watchlist.user_id == current_user.id)
        .scalar()
    )

    if existing_count >= 10:
        raise HTTPException(
            status_code=400, detail="Maximum watchlist limit (10) reached"
        )

    # Create watchlist
    watchlist = Watchlist(name=name, user_id=current_user.id)
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    return WatchlistResponse(
        id=watchlist.id, name=watchlist.name, created_at=watchlist.created_at
    )


@router.delete("/{watchlist_id}", status_code=204)
async def delete_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a watchlist.

    Args:
        watchlist_id: Watchlist ID to delete
        current_user: Authenticated user
        db: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException: If watchlist not found or not owned by user
    """
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    db.delete(watchlist)
    db.commit()

    return None


@router.get("/{watchlist_id}/items", response_model=list[WatchlistItemResponse])
async def get_watchlist_items(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all items in a watchlist.

    Args:
        watchlist_id: Watchlist ID
        current_user: Authenticated user
        db: Database session

    Returns:
        List of watchlist items

    Raises:
        HTTPException: If watchlist not found or not owned by user
    """
    # Verify watchlist belongs to user
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Get all items
    items = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.added_at.desc())
        .all()
    )

    return [
        WatchlistItemResponse(id=item.id, symbol=item.symbol, added_at=item.added_at)
        for item in items
    ]


@router.post("/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=201)
async def add_item_to_watchlist(
    watchlist_id: int,
    request: AddItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a stock to a watchlist.

    Args:
        watchlist_id: Watchlist ID
        request: Add item request with symbol
        current_user: Authenticated user
        db: Database session

    Returns:
        Created watchlist item

    Raises:
        HTTPException: If watchlist not found, not owned by user, item already exists, or limit reached
    """
    # Verify watchlist exists and belongs to user
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Validate symbol
    symbol = validate_symbol(request.symbol)

    # Check if item already exists
    existing_item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.symbol == symbol)
        .first()
    )

    if existing_item:
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")

    # Check item limit (50 max per watchlist)
    item_count = (
        db.query(func.count(WatchlistItem.id))
        .filter(WatchlistItem.watchlist_id == watchlist_id)
        .scalar()
    )

    if item_count >= 50:
        raise HTTPException(
            status_code=400, detail="Maximum items per watchlist (50) reached"
        )

    # Create item
    item = WatchlistItem(watchlist_id=watchlist_id, symbol=symbol)
    db.add(item)
    db.commit()
    db.refresh(item)

    return WatchlistItemResponse(id=item.id, symbol=item.symbol, added_at=item.added_at)


@router.delete("/{watchlist_id}/items/{item_id}", status_code=204)
async def remove_item_from_watchlist(
    watchlist_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a stock from a watchlist.

    Args:
        watchlist_id: Watchlist ID
        item_id: Item ID to remove
        current_user: Authenticated user
        db: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException: If watchlist or item not found
    """
    # Verify watchlist belongs to user
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Find and delete item
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.id == item_id, WatchlistItem.watchlist_id == watchlist_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in watchlist")

    db.delete(item)
    db.commit()

    return None
