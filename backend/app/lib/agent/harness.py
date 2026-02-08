"""AI agent harness using Anthropic API with tool use."""
import json
import logging
from typing import AsyncGenerator

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.lib.agent.prompts import build_system_prompt
from app.lib.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from app.lib.agent.skills import SkillManager
from app.models.memory_fact import MemoryFact
from app.models.user import User

logger = logging.getLogger(__name__)

# Maximum tool use iterations to prevent runaway loops
MAX_TOOL_ITERATIONS = 10


class InvestmentAgent:
    """Manages agent lifecycle for a user session."""

    def __init__(self, user_id: int, db: Session, conversation_id: int | None = None):
        self.user_id = user_id
        self.db = db
        self.conversation_id = conversation_id
        self.tool_executor = ToolExecutor(db, user_id)
        self.skill_manager = SkillManager(db, user_id)
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Build system prompt with memory
        memory_facts = self._get_memory_facts()
        self.system_prompt = build_system_prompt(memory_facts)

    def _get_memory_facts(self) -> list[dict]:
        """Get user's memory facts for system prompt injection."""
        user = self.db.query(User).filter(User.id == self.user_id).first()
        if not user or not user.ai_memory_enabled:
            return []

        facts = (
            self.db.query(MemoryFact)
            .filter(MemoryFact.user_id == self.user_id)
            .all()
        )
        return [{"type": f.fact_type, "content": f.content} for f in facts]

    async def stream_response(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[dict, None]:
        """Stream agent response with tool use support.

        Yields event dicts:
        - {"type": "token", "content": "..."}
        - {"type": "tool_call", "tool": "...", "input": {...}}
        - {"type": "tool_result", "tool": "...", "output": {...}}
        - {"type": "action_proposed", "action_id": ..., "description": "..."}
        - {"type": "done", "content": "...", "usage": {...}}
        - {"type": "error", "message": "..."}
        """
        iteration = 0
        current_messages = list(messages)

        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            full_response_text = ""

            try:
                async with self.client.messages.stream(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=current_messages,
                    tools=TOOL_DEFINITIONS,
                ) as stream:
                    async for event in stream:
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                full_response_text += event.delta.text
                                yield {"type": "token", "content": event.delta.text}

                    # Get the final message to check for tool use
                    final_message = await stream.get_final_message()

            except anthropic.APIError as e:
                yield {"type": "error", "message": f"API error: {str(e)}"}
                return

            # Check if we need to handle tool calls
            has_tool_use = any(
                block.type == "tool_use" for block in final_message.content
            )

            if not has_tool_use:
                # No tool calls - we're done
                yield {
                    "type": "done",
                    "content": full_response_text,
                    "usage": {
                        "input_tokens": final_message.usage.input_tokens,
                        "output_tokens": final_message.usage.output_tokens,
                    },
                }
                return

            # Process tool calls
            tool_results = []
            for block in final_message.content:
                if block.type == "tool_use":
                    yield {
                        "type": "tool_call",
                        "tool": block.name,
                        "input": block.input,
                        "tool_use_id": block.id,
                    }

                    # Inject conversation_id for propose_action
                    tool_input = dict(block.input)
                    if block.name == "propose_action" and self.conversation_id:
                        tool_input["_conversation_id"] = self.conversation_id

                    # Execute the tool
                    result = await self.tool_executor.execute(block.name, tool_input)

                    # Check if this was a proposed action
                    if block.name == "propose_action":
                        try:
                            result_data = (
                                json.loads(result)
                                if isinstance(result, str)
                                else result
                            )
                            if isinstance(result_data, dict) and result_data.get(
                                "requires_confirmation"
                            ):
                                yield {
                                    "type": "action_proposed",
                                    "action_id": result_data["pending_action_id"],
                                    "description": result_data["description"],
                                    "action_type": result_data["action_type"],
                                }
                        except (json.JSONDecodeError, KeyError):
                            pass

                    yield {
                        "type": "tool_result",
                        "tool": block.name,
                        "output": result,
                        "tool_use_id": block.id,
                    }

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": (
                            result if isinstance(result, str) else json.dumps(result)
                        ),
                    })

            # Add assistant message and tool results to continue the loop
            assistant_content = [
                block
                for block in [
                    (
                        {"type": "text", "text": full_response_text}
                        if full_response_text
                        else None
                    ),
                    *[
                        {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                        for block in final_message.content
                        if block.type == "tool_use"
                    ],
                ]
                if block is not None
            ]

            current_messages.append({
                "role": "assistant",
                "content": assistant_content,
            })
            current_messages.append({
                "role": "user",
                "content": tool_results,
            })

        # Max iterations reached
        yield {"type": "error", "message": "Maximum tool iterations reached"}


async def extract_memory_facts(
    content: str,
    user_id: int,
) -> list[dict]:
    """Extract memory facts from conversation using a cheap model call.

    Returns list of dicts: [{"fact_type": "...", "content": "..."}]
    """
    if not settings.ANTHROPIC_API_KEY:
        return []

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = await client.messages.create(
            model="claude-haiku-3-20240307",
            max_tokens=500,
            system=(
                "Extract any important facts about the user from this conversation.\n"
                'Return a JSON array of objects with "fact_type" and "content" fields.\n'
                "fact_type must be one of: preference, portfolio, strategy, risk_tolerance.\n"
                "Only extract clear, definitive facts. Return [] if none found.\n"
                'Example: [{"fact_type": "preference", "content": "Prefers tech stocks"}]'
            ),
            messages=[{"role": "user", "content": content}],
        )

        result_text = response.content[0].text.strip()
        # Try to parse JSON from the response
        if result_text.startswith("["):
            return json.loads(result_text)
        return []
    except Exception as e:
        logger.error(f"Memory extraction failed: {e}")
        return []
