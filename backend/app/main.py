"""FastAPI application setup."""
import os
from pathlib import Path
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, watchlists, securities, market, chat, skills
from app.routes import settings as settings_routes
from app.routes import etf as etf_routes

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
app.include_router(market.router, prefix="/api/market", tags=["Market"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["Settings"])
app.include_router(etf_routes.router, prefix="/api/etf", tags=["ETF"])


@app.on_event("startup")
async def init_database():
    """Auto-create tables in SQLite mode (replaces Alembic)."""
    if settings.SINGLE_USER_MODE or settings.is_sqlite:
        from app.database import init_db
        init_db()
        print(f"✓ Database initialized ({settings.DATABASE_URL})")


@app.on_event("startup")
async def configure_openbb():
    """Configure OpenBB API credentials on startup."""
    fmp_api_key = os.getenv("FMP_API_KEY") or settings.OPENBB_API_KEY

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


@app.on_event("startup")
async def start_fmp_mcp():
    """Start the FMP MCP server for enhanced financial data access."""
    try:
        from app.lib.fmp_mcp import fmp_mcp
        api_key = settings.OPENBB_API_KEY
        success = await fmp_mcp.start(api_key)
        if success:
            tools = await fmp_mcp.get_tools()
            print(f"✓ FMP MCP server started ({len(tools)} tools available)")
        else:
            print("⚠ FMP MCP server unavailable (agent uses built-in tools only)")
    except Exception as e:
        print(f"⚠ FMP MCP startup error: {e}")


@app.on_event("shutdown")
async def stop_fmp_mcp():
    """Stop the FMP MCP server gracefully."""
    try:
        from app.lib.fmp_mcp import fmp_mcp
        await fmp_mcp.stop()
    except Exception:
        pass


@app.on_event("startup")
async def start_scheduler():
    """Start the background market-data refresh scheduler."""
    try:
        from app.lib.scheduler import scheduler
        scheduler.start()
        print("✓ Background scheduler started")
    except Exception as e:
        print(f"⚠ Scheduler failed to start: {e}")


@app.on_event("shutdown")
async def stop_scheduler():
    """Shut down the background scheduler gracefully."""
    try:
        from app.lib.scheduler import scheduler
        if scheduler.running:
            scheduler.shutdown(wait=False)
            print("✓ Background scheduler stopped")
    except Exception:
        pass


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
