"""AI agent harness using LiteLLM for multi-provider streaming.

Port of Dexter's scratchpad-backed context management architecture.
"""
import json
import logging
from typing import AsyncGenerator

import litellm
from sqlalchemy.orm import Session

from app.config import settings
from app.lib.agent.prompts import build_system_prompt, build_iteration_prompt
from app.lib.agent.scratchpad import Scratchpad
from app.lib.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from app.lib.agent.tool_adapter import anthropic_tools_to_openai, convert_messages_to_openai
from app.lib.agent.models import DEFAULT_MODEL, MEMORY_EXTRACTION_MODEL, MODEL_IDS, MODEL_REGISTRY
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


def _get_api_key_for_model(model_id: str) -> str | None:
    """Get the API key for the given model from config/env."""
    for entry in MODEL_REGISTRY:
        if entry["id"] == model_id:
            config_key = entry["config_key"]
            if config_key == "anthropic_api_key":
                return settings.ANTHROPIC_API_KEY or None
            elif config_key == "openai_api_key":
                return settings.OPENAI_API_KEY or None
            elif config_key == "google_api_key":
                return settings.GOOGLE_API_KEY or None
            elif config_key == "groq_api_key":
                return settings.GROQ_API_KEY or None
    return None


class InvestmentAgent:
    """Manages agent lifecycle for a user session."""

    def __init__(self, user_id: int, db: Session, conversation_id: int | None = None, model: str | None = None):
        self.user_id = user_id
        self.db = db
        self.conversation_id = conversation_id
        self.model = model if model and model in MODEL_IDS else DEFAULT_MODEL

        self.skill_manager = SkillManager(db, user_id)
        self.tool_executor = ToolExecutor(db, user_id, skill_manager=self.skill_manager)

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

    def _build_litellm_kwargs(self, messages: list[dict], tools: list[dict]) -> dict:
        """Build kwargs for litellm.acompletion call."""
        openai_messages = convert_messages_to_openai(messages, self.system_prompt)
        openai_tools = anthropic_tools_to_openai(tools) if tools else []
        api_key = _get_api_key_for_model(self.model)
        kwargs: dict = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": 4096,
            "stream": True,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if openai_tools:
            kwargs["tools"] = openai_tools
            kwargs["tool_choice"] = "auto"
        return kwargs

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
            kwargs = self._build_litellm_kwargs(api_messages, all_tools)

            try:
                response_stream = await litellm.acompletion(**kwargs)
                finish_reason = None
                pending_tool_calls: dict[int, dict] = {}  # index -> accumulated call
                last_chunk = None

                async for chunk in response_stream:
                    last_chunk = chunk
                    choice = chunk.choices[0]
                    delta = choice.delta
                    finish_reason = choice.finish_reason or finish_reason

                    if delta.content:
                        full_response_text += delta.content
                        yield {"type": "token", "content": delta.content}

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in pending_tool_calls:
                                pending_tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.id:
                                pending_tool_calls[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    pending_tool_calls[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    pending_tool_calls[idx]["arguments"] += tc.function.arguments

                usage = getattr(last_chunk, "usage", None) if last_chunk else None

            except litellm.ContextWindowExceededError as e:
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
            except Exception as e:
                yield {"type": "error", "message": f"API error: {str(e)}"}
                return

            # No tool calls → done
            if not pending_tool_calls:
                yield {
                    "type": "done",
                    "content": full_response_text,
                    "usage": {
                        "input_tokens": usage.prompt_tokens if usage else 0,
                        "output_tokens": usage.completion_tokens if usage else 0,
                    },
                }
                return

            # Process tool calls
            for idx in sorted(pending_tool_calls.keys()):
                tc = pending_tool_calls[idx]
                tool_name = tc["name"]
                tool_use_id = tc["id"]
                try:
                    tool_input = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    tool_input = {}

                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "input": tool_input,
                    "tool_use_id": tool_use_id,
                }

                # Skill deduplication (matches Dexter tool-executor.ts pattern)
                if tool_name == "skill":
                    skill_name = tool_input.get("skill", "")
                    if scratchpad.has_executed_skill(skill_name):
                        logger.debug(f"Skipping already-executed skill: {skill_name}")
                        continue

                # Soft limit check
                query_arg = _extract_query_from_args(tool_input)
                limit_check = scratchpad.can_call_tool(tool_name, query_arg)
                if limit_check.get("warning"):
                    yield {
                        "type": "tool_limit",
                        "tool": tool_name,
                        "warning": limit_check["warning"],
                        "blocked": False,
                    }

                # Inject conversation_id for propose_action
                if tool_name == "propose_action" and self.conversation_id:
                    tool_input["_conversation_id"] = self.conversation_id

                result = await self.tool_executor.execute(tool_name, tool_input)

                # Record in scratchpad
                scratchpad.record_tool_call(tool_name, query_arg)
                scratchpad.add_tool_result(tool_name, tool_input, result)

                # propose_action event
                if tool_name == "propose_action":
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
                    "tool": tool_name,
                    "output": result,
                    "tool_use_id": tool_use_id,
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

    try:
        response = await litellm.acompletion(
            model=MEMORY_EXTRACTION_MODEL,
            max_tokens=500,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract any important facts about the user from this conversation.\n"
                        'Return a JSON array of objects with "fact_type" and "content" fields.\n'
                        "fact_type must be one of: preference, portfolio, strategy, risk_tolerance.\n"
                        "Only extract clear, definitive facts. Return [] if none found.\n"
                        'Example: [{"fact_type": "preference", "content": "Prefers tech stocks"}]'
                    ),
                },
                {"role": "user", "content": content},
            ],
            api_key=settings.ANTHROPIC_API_KEY,
            stream=False,
        )
        result_text = response.choices[0].message.content.strip()
        if result_text.startswith("["):
            return json.loads(result_text)
        return []
    except Exception as e:
        logger.error(f"Memory extraction failed: {e}")
        return []
