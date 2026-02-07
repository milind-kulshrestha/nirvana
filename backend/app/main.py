"""FastAPI application setup."""
import os
from pathlib import Path
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, watchlists, securities, chat, skills

# Create FastAPI app
app = FastAPI(
    title="Financial Tracker API",
    description="Stock watchlist tracker with live market data",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(watchlists.router, prefix="/api/watchlists", tags=["Watchlists"])
app.include_router(securities.router, prefix="/api/securities", tags=["Securities"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])


@app.on_event("startup")
async def configure_openbb():
    """Configure OpenBB API credentials on startup."""
    fmp_api_key = os.getenv("FMP_API_KEY")

    if fmp_api_key:
        # Create OpenBB user settings directory
        openbb_dir = Path.home() / ".openbb_platform"
        openbb_dir.mkdir(exist_ok=True)

        settings_file = openbb_dir / "user_settings.json"

        # Load or create settings
        if settings_file.exists():
            with open(settings_file, "r") as f:
                settings_data = json.load(f)
        else:
            settings_data = {
                "credentials": {},
                "preferences": {},
                "defaults": {"commands": {}}
            }

        # Update FMP API key
        settings_data["credentials"]["fmp_api_key"] = fmp_api_key

        # Write settings
        with open(settings_file, "w") as f:
            json.dump(settings_data, f, indent=4)

        print(f"✓ OpenBB configured with FMP API key")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Financial Tracker API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
