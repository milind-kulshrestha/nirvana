"""AI agent harness using Anthropic API with tool use.

Port of Dexter's scratchpad-backed context management architecture.
"""
import json
import logging
from typing import AsyncGenerator

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.lib.agent.prompts import build_system_prompt, build_iteration_prompt
from app.lib.agent.scratchpad import Scratchpad
from app.lib.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from app.lib.fmp_mcp import fmp_mcp
from app.lib.agent.skills import SkillManager
from app.models.memory_fact import MemoryFact
from app.models.user import User

logger = logging.getLogger(__name__)

# Context management constants (matching Dexter exactly)
CONTEXT_THRESHOLD = 100_000    # tokens; trigger context clearing
KEEP_TOOL_USES = 5             # most recent results to keep at threshold
MAX_OVERFLOW_RETRIES = 2       # on hard context overflow errors
OVERFLOW_KEEP_TOOL_USES = 3   # keep even fewer on hard overflow


class InvestmentAgent:
    """Manages agent lifecycle for a user session."""

    def __init__(self, user_id: int, db: Session, conversation_id: int | None = None):
        self.user_id = user_id
        self.db = db
        self.conversation_id = conversation_id

        self.skill_manager = SkillManager(db, user_id)
        self.tool_executor = ToolExecutor(db, user_id, skill_manager=self.skill_manager)
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Build system prompt with memory and available skills
        memory_facts = self._get_memory_facts()
        available_skills = self.skill_manager.get_skills_for_prompt()
        self.system_prompt = build_system_prompt(memory_facts, available_skills)

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
        - {"type": "tool_limit", "tool": "...", "warning": "...", "blocked": false}
        - {"type": "context_cleared", "cleared_count": N, "kept_count": N}
        - {"type": "done", "content": "...", "usage": {...}}
        - {"type": "error", "message": "..."}
        """
        # Merge native tools with any FMP MCP tools that are available
        fmp_tools = await fmp_mcp.get_tools()
        all_tools = TOOL_DEFINITIONS + fmp_tools

        # Extract query from last user message
        last_message = messages[-1]
        raw_content = last_message.get("content", "")
        if isinstance(raw_content, list):
            # Multi-part content — concatenate text blocks
            query_text = " ".join(
                block.get("text", "") for block in raw_content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        else:
            query_text = str(raw_content)

        scratchpad = Scratchpad(query_text)

        # Prior conversation turns are static context; we rebuild the last user turn each iteration
        context_messages = list(messages[:-1])
        current_prompt = query_text  # iteration 1: raw query
        overflow_retries = 0
        iteration = 0

        while True:
            iteration += 1
            full_response_text = ""

            api_messages = context_messages + [{"role": "user", "content": current_prompt}]

            try:
                async with self.client.messages.stream(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=api_messages,
                    tools=all_tools,
                ) as stream:
                    async for event in stream:
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                full_response_text += event.delta.text
                                yield {"type": "token", "content": event.delta.text}

                    final_message = await stream.get_final_message()

            except anthropic.BadRequestError as e:
                # Hard context overflow
                if overflow_retries < MAX_OVERFLOW_RETRIES:
                    overflow_retries += 1
                    logger.warning(f"Context overflow (retry {overflow_retries}): {e}")
                    scratchpad.clear_oldest_tool_results(OVERFLOW_KEEP_TOOL_USES)
                    current_prompt = build_iteration_prompt(
                        query_text,
                        scratchpad.get_tool_results(),
                        scratchpad.format_tool_usage_for_prompt(),
                    )
                    continue
                else:
                    yield {"type": "error", "message": f"Context overflow after retries: {str(e)}"}
                    return
            except anthropic.APIError as e:
                yield {"type": "error", "message": f"API error: {str(e)}"}
                return

            # Check if we need to handle tool calls
            has_tool_use = any(
                block.type == "tool_use" for block in final_message.content
            )

            if not has_tool_use:
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
            for block in final_message.content:
                if block.type != "tool_use":
                    continue

                yield {
                    "type": "tool_call",
                    "tool": block.name,
                    "input": block.input,
                    "tool_use_id": block.id,
                }

                # Skill deduplication (matches Dexter tool-executor.ts pattern)
                if block.name == "skill":
                    skill_name = block.input.get("skill", "")
                    if scratchpad.has_executed_skill(skill_name):
                        logger.debug(f"Skipping already-executed skill: {skill_name}")
                        continue

                # Soft limit check
                query_arg = _extract_query_from_args(block.input)
                limit_check = scratchpad.can_call_tool(block.name, query_arg)
                if limit_check.get("warning"):
                    yield {
                        "type": "tool_limit",
                        "tool": block.name,
                        "warning": limit_check["warning"],
                        "blocked": False,
                    }

                # Inject conversation_id for propose_action
                tool_input = dict(block.input)
                if block.name == "propose_action" and self.conversation_id:
                    tool_input["_conversation_id"] = self.conversation_id

                result = await self.tool_executor.execute(block.name, tool_input)

                # Record in scratchpad
                scratchpad.record_tool_call(block.name, query_arg)
                scratchpad.add_tool_result(block.name, dict(block.input), result)

                # propose_action event
                if block.name == "propose_action":
                    try:
                        result_data = (
                            json.loads(result) if isinstance(result, str) else result
                        )
                        if isinstance(result_data, dict) and result_data.get("requires_confirmation"):
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

            # Context threshold management
            if scratchpad.estimate_tokens(self.system_prompt, query_text) > CONTEXT_THRESHOLD:
                cleared = scratchpad.clear_oldest_tool_results(KEEP_TOOL_USES)
                if cleared > 0:
                    yield {
                        "type": "context_cleared",
                        "cleared_count": cleared,
                        "kept_count": KEEP_TOOL_USES,
                    }

            # Rebuild iteration prompt with accumulated tool results
            current_prompt = build_iteration_prompt(
                query_text,
                scratchpad.get_tool_results(),
                scratchpad.format_tool_usage_for_prompt(),
            )
            overflow_retries = 0  # reset on successful iteration

            logger.debug(f"Iteration {iteration} complete, prompt[:200]: {current_prompt[:200]}")


def _extract_query_from_args(args: dict) -> str | None:
    """Extract a query string from tool input args for similarity tracking."""
    for key in ("query", "search", "question", "q", "text", "input", "symbol"):
        val = args.get(key)
        if isinstance(val, str):
            return val
    return None


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
        if result_text.startswith("["):
            return json.loads(result_text)
        return []
    except Exception as e:
        logger.error(f"Memory extraction failed: {e}")
        return []
