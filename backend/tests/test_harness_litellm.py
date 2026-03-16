import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_chunk(content=None, tool_calls=None, finish_reason=None):
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = content
    chunk.choices[0].delta.tool_calls = tool_calls
    chunk.choices[0].finish_reason = finish_reason
    chunk.usage = MagicMock(prompt_tokens=10, completion_tokens=5) if finish_reason else None
    return chunk


@pytest.mark.asyncio
async def test_stream_yields_token_and_done():
    from app.lib.agent.harness import InvestmentAgent

    async def fake_acompletion(**kwargs):
        async def _gen():
            yield _make_chunk(content="Hello")
            yield _make_chunk(finish_reason="stop")
        return _gen()

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.lib.agent.harness.litellm.acompletion", side_effect=fake_acompletion):
        with patch("app.lib.agent.harness.fmp_mcp.get_tools", new_callable=AsyncMock, return_value=[]):
            agent = InvestmentAgent.__new__(InvestmentAgent)
            agent.user_id = 1
            agent.db = db
            agent.conversation_id = None
            agent.model = "anthropic/claude-sonnet-4-6"
            agent.system_prompt = "You are helpful."
            agent.tool_executor = MagicMock()
            agent.skill_manager = MagicMock()
            agent.skill_manager.get_skills_for_prompt.return_value = ""

            events = []
            async for event in agent.stream_response([{"role": "user", "content": "hi"}]):
                events.append(event)

    types = [e["type"] for e in events]
    assert "token" in types
    assert "done" in types
    assert any(e["content"] == "Hello" for e in events if e["type"] == "token")
