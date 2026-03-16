"""Model registry — single source of truth for all supported LLM models."""

MODEL_REGISTRY = [
    {"id": "anthropic/claude-sonnet-4-6",         "display_name": "Claude Sonnet 4.6",   "provider": "anthropic", "config_key": "anthropic_api_key"},
    {"id": "anthropic/claude-opus-4-6",            "display_name": "Claude Opus 4.6",     "provider": "anthropic", "config_key": "anthropic_api_key"},
    {"id": "anthropic/claude-haiku-4-5-20251001",  "display_name": "Claude Haiku 4.5",    "provider": "anthropic", "config_key": "anthropic_api_key"},
    {"id": "gpt-4o",                               "display_name": "GPT-4o",              "provider": "openai",    "config_key": "openai_api_key"},
    {"id": "gpt-4o-mini",                          "display_name": "GPT-4o Mini",         "provider": "openai",    "config_key": "openai_api_key"},
    {"id": "gemini/gemini-2.0-flash",              "display_name": "Gemini 2.0 Flash",    "provider": "google",    "config_key": "google_api_key"},
    {"id": "gemini/gemini-1.5-pro",                "display_name": "Gemini 1.5 Pro",      "provider": "google",    "config_key": "google_api_key"},
    {"id": "groq/llama-3.3-70b-versatile",         "display_name": "Llama 3.3 70B",       "provider": "groq",      "config_key": "groq_api_key"},
]

DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"
MEMORY_EXTRACTION_MODEL = "anthropic/claude-haiku-4-5-20251001"
MODEL_IDS = {m["id"] for m in MODEL_REGISTRY}
