"""Convert between Anthropic and LiteLLM/OpenAI tool/message formats."""


def anthropic_tools_to_openai(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


def convert_messages_to_openai(messages: list[dict], system_prompt: str | None = None) -> list[dict]:
    result = []
    if system_prompt:
        result.append({"role": "system", "content": system_prompt})
    result.extend(messages)
    return result
