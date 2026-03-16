from app.lib.config_manager import DEFAULT_CONFIG, SECRET_KEYS


def test_default_config_has_provider_keys():
    assert "openai_api_key" in DEFAULT_CONFIG
    assert "google_api_key" in DEFAULT_CONFIG
    assert "groq_api_key" in DEFAULT_CONFIG
    assert "default_model" in DEFAULT_CONFIG


def test_provider_keys_are_secrets():
    assert "openai_api_key" in SECRET_KEYS
    assert "google_api_key" in SECRET_KEYS
    assert "groq_api_key" in SECRET_KEYS


def test_default_model_is_not_a_secret():
    assert "default_model" not in SECRET_KEYS
