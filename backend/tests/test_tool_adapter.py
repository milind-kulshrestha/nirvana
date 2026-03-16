from app.lib.agent.tool_adapter import anthropic_tools_to_openai, convert_messages_to_openai

ANTHROPIC_TOOL = {
    "name": "get_quote",
    "description": "Get real-time quote",
    "input_schema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]},
}
OPENAI_TOOL = {
    "type": "function",
    "function": {
        "name": "get_quote",
        "description": "Get real-time quote",
        "parameters": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]},
    },
}


def test_anthropic_tools_to_openai():
    assert anthropic_tools_to_openai([ANTHROPIC_TOOL]) == [OPENAI_TOOL]


def test_convert_messages_prepends_system():
    result = convert_messages_to_openai([{"role": "user", "content": "hi"}], system_prompt="be helpful")
    assert result[0] == {"role": "system", "content": "be helpful"}
    assert result[1] == {"role": "user", "content": "hi"}


def test_convert_messages_no_system():
    result = convert_messages_to_openai([{"role": "user", "content": "hi"}])
    assert result[0]["role"] == "user"
