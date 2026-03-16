import pytest
from fastapi.testclient import TestClient


def test_update_settings_accepts_provider_keys():
    from app.routes.settings import UpdateSettingsRequest
    req = UpdateSettingsRequest(openai_api_key="sk-test", default_model="gpt-4o")
    assert req.openai_api_key == "sk-test"
    assert req.default_model == "gpt-4o"


def test_models_endpoint_returns_registry():
    from fastapi import FastAPI
    from app.routes.settings import router

    app = FastAPI()
    app.include_router(router, prefix="/api/settings")
    client = TestClient(app)

    res = client.get("/api/settings/models")
    assert res.status_code == 200
    data = res.json()
    ids = [m["id"] for m in data]
    assert "anthropic/claude-sonnet-4-6" in ids
    assert "gpt-4o" in ids
    for m in data:
        assert "display_name" in m
        assert "provider" in m
        assert "config_key" not in m
