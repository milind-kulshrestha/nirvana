"""Settings routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.lib.config_manager import config_manager, mask_secret, SECRET_KEYS

router = APIRouter()


class UpdateSettingsRequest(BaseModel):
    anthropic_api_key: Optional[str] = None
    fmp_api_key: Optional[str] = None
    refresh_interval_minutes: Optional[int] = None
    market_hours_only: Optional[bool] = None


@router.get("")
async def get_settings():
    """Return current settings with secret keys masked."""
    config = config_manager.get_all()
    masked = {}
    for key, value in config.items():
        if key in SECRET_KEYS:
            masked[key] = mask_secret(value)
        else:
            masked[key] = value
    return masked


@router.put("")
async def update_settings(req: UpdateSettingsRequest):
    """Update settings and save to config.json."""
    # Only include fields that were explicitly provided
    updates = req.model_dump(exclude_none=True)
    config = config_manager.update(updates)

    # Return masked version
    masked = {}
    for key, value in config.items():
        if key in SECRET_KEYS:
            masked[key] = mask_secret(value)
        else:
            masked[key] = value
    return masked


@router.get("/status")
async def get_settings_status():
    """Check config status for first-run detection."""
    return {
        "config_exists": config_manager.config_exists(),
        "missing_keys": config_manager.get_missing_keys(),
    }
