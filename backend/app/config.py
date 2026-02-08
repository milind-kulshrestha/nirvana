"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # App
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SINGLE_USER_MODE: bool = os.getenv("SINGLE_USER_MODE", "false").lower() == "true"

    # Database
    _sqlite_url = "sqlite:///" + os.path.join(
        os.path.expanduser("~"), ".nirvana", "nirvana.db"
    )

    @property
    def DATABASE_URL(self) -> str:
        explicit = os.getenv("DATABASE_URL")
        if self.SINGLE_USER_MODE and (not explicit or explicit.startswith("postgresql")):
            return self._sqlite_url
        return explicit or self._sqlite_url

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    # OpenBB
    OPENBB_API_KEY: str = os.getenv("OPENBB_API_KEY", "")

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")


settings = Settings()
