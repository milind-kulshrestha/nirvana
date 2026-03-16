"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

# Import config_manager lazily to avoid circular imports
_config_manager = None


def _get_config_manager():
    global _config_manager
    if _config_manager is None:
        from app.lib.config_manager import config_manager
        _config_manager = config_manager
    return _config_manager


class Settings:
    """Application settings.

    Priority: environment variables > config.json > defaults.
    """

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

    # OpenBB / FMP - env var overrides config.json
    @property
    def OPENBB_API_KEY(self) -> str:
        env_val = os.getenv("OPENBB_API_KEY") or os.getenv("FMP_API_KEY")
        if env_val:
            return env_val
        return _get_config_manager().get("fmp_api_key", "")

    # Anthropic - env var overrides config.json
    @property
    def ANTHROPIC_API_KEY(self) -> str:
        env_val = os.getenv("ANTHROPIC_API_KEY")
        if env_val:
            return env_val
        return _get_config_manager().get("anthropic_api_key", "")

    @property
    def OPENAI_API_KEY(self) -> str:
        return os.getenv("OPENAI_API_KEY") or _get_config_manager().get("openai_api_key", "")

    @property
    def GOOGLE_API_KEY(self) -> str:
        return os.getenv("GOOGLE_API_KEY") or _get_config_manager().get("google_api_key", "")

    @property
    def GROQ_API_KEY(self) -> str:
        return os.getenv("GROQ_API_KEY") or _get_config_manager().get("groq_api_key", "")

    @property
    def DEFAULT_MODEL(self) -> str:
        return os.getenv("DEFAULT_MODEL") or _get_config_manager().get("default_model", "anthropic/claude-sonnet-4-6")

    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")


settings = Settings()
