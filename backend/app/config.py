"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # App
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/watchlist"
    )

    # OpenBB
    OPENBB_API_KEY: str = os.getenv("OPENBB_API_KEY", "")

    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")


settings = Settings()
