import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def test_send_message_request_accepts_model():
    from app.routes.chat import SendMessageRequest
    req = SendMessageRequest(content="hi", model="gpt-4o")
    assert req.model == "gpt-4o"


def test_send_message_request_model_defaults_to_none():
    from app.routes.chat import SendMessageRequest
    req = SendMessageRequest(content="hi")
    assert req.model is None


@pytest.mark.asyncio
async def test_stream_chat_passes_model_to_agent():
    from app.services.chat_service import ChatService
    captured = {}

    class FakeAgent:
        def __init__(self, user_id, db, conversation_id, model=None):
            captured["model"] = model

        async def stream_response(self, messages):
            yield {"type": "done", "content": "ok", "usage": {}}

    db = MagicMock()
    service = ChatService(db, user_id=1)
    conv = MagicMock()
    conv.id = 1
    conv.title = None

    with patch("app.services.chat_service.InvestmentAgent", FakeAgent):
        with patch.object(service, "get_conversation_messages", return_value=[{"role": "user", "content": "hi"}]):
            with patch.object(service, "save_user_message"):
                with patch.object(service, "save_assistant_message"):
                    with patch.object(service, "_extract_memory", new_callable=AsyncMock, return_value=None) if hasattr(ChatService, "_extract_memory") else patch("app.services.chat_service.extract_memory_facts", new_callable=AsyncMock, return_value=[]):
                        async for _ in service.stream_chat(conv, "hi", model="gpt-4o"):
                            pass

    assert captured["model"] == "gpt-4o"
