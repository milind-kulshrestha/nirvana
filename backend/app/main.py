"""FastAPI application setup."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, watchlists, securities

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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(watchlists.router, prefix="/api/watchlists", tags=["Watchlists"])
app.include_router(securities.router, prefix="/api/securities", tags=["Securities"])


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
