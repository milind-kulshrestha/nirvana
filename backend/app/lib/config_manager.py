"""Configuration manager for ~/.nirvana/config.json."""
import json
import os
import threading
from pathlib import Path
from typing import Any, Optional


# Default configuration schema
DEFAULT_CONFIG = {
    "anthropic_api_key": "",
    "openai_api_key": "",
    "google_api_key": "",
    "groq_api_key": "",
    "fmp_api_key": "",
    "default_model": "anthropic/claude-sonnet-4-6",
    "refresh_interval_minutes": 15,
    "market_hours_only": True,
}

# Keys that contain secrets (should be masked in GET responses)
SECRET_KEYS = {"anthropic_api_key", "openai_api_key", "google_api_key", "groq_api_key", "fmp_api_key"}

CONFIG_DIR = Path.home() / ".nirvana"
CONFIG_PATH = CONFIG_DIR / "config.json"


class ConfigManager:
    """Thread-safe manager for ~/.nirvana/config.json."""

    def __init__(self):
        self._lock = threading.RLock()
        self._cache: dict[str, Any] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load config from disk if not already cached."""
        if not self._loaded:
            self._load()

    def _load(self) -> None:
        """Read config.json from disk into cache."""
        with self._lock:
            if CONFIG_PATH.exists():
                try:
                    with open(CONFIG_PATH, "r") as f:
                        data = json.load(f)
                    # Merge with defaults so new keys are always present
                    self._cache = {**DEFAULT_CONFIG, **data}
                except (json.JSONDecodeError, OSError):
                    self._cache = dict(DEFAULT_CONFIG)
            else:
                self._cache = dict(DEFAULT_CONFIG)
            self._loaded = True

    def _save(self) -> None:
        """Write current cache to config.json on disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(self._cache, f, indent=2)

    def get_all(self) -> dict[str, Any]:
        """Return a copy of the full config dict."""
        with self._lock:
            self._ensure_loaded()
            return dict(self._cache)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a single config value."""
        with self._lock:
            self._ensure_loaded()
            return self._cache.get(key, default)

    def update(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Update config with provided key/value pairs, save, and return new config."""
        with self._lock:
            self._ensure_loaded()
            # Only allow known keys
            for key, value in updates.items():
                if key in DEFAULT_CONFIG:
                    self._cache[key] = value
            self._save()
            return dict(self._cache)

    def config_exists(self) -> bool:
        """Check whether config.json exists on disk."""
        return CONFIG_PATH.exists()

    def get_missing_keys(self) -> list[str]:
        """Return list of required secret keys that are empty or missing."""
        with self._lock:
            self._ensure_loaded()
            missing = []
            for key in SECRET_KEYS:
                val = self._cache.get(key, "")
                if not val:
                    missing.append(key)
            return missing

    def reload(self) -> None:
        """Force reload from disk (useful after external changes)."""
        self._loaded = False
        self._load()


def mask_secret(value: str) -> str:
    """Mask a secret string, showing first 3 and last 3 chars.

    Examples:
        "sk-ant-abc123xyz" -> "sk-...xyz"
        "short" -> "***"
        "" -> ""
    """
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}...{value[-3:]}"


# Singleton instance
config_manager = ConfigManager()
