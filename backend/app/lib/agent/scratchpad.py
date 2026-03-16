"""Append-only JSONL scratchpad for agent work on a single query.

Port of Dexter's src/agent/scratchpad.ts.
"""
import json
import logging
import re
import string
from datetime import datetime, timezone
from hashlib import md5
from pathlib import Path

logger = logging.getLogger(__name__)

_NIRVANA_DIR = Path.home() / ".nirvana"


class Scratchpad:
    """Append-only JSONL log of agent work on a single query.

    File: ~/.nirvana/scratchpad/{timestamp}_{md5_12}.jsonl
    Context clearing is in-memory only — file is never modified.
    """

    _max_calls_per_tool: int = 3
    _similarity_threshold: float = 0.7

    def __init__(self, query: str):
        self._scratchpad_dir = _NIRVANA_DIR / "scratchpad"
        self._scratchpad_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        query_hash = md5(query.encode()).hexdigest()[:12]
        self._filepath = self._scratchpad_dir / f"{timestamp}_{query_hash}.jsonl"

        self._tool_call_counts: dict[str, int] = {}
        self._tool_queries: dict[str, list[str]] = {}
        self._cleared_tool_indices: set[int] = set()

        self._append({
            "type": "init",
            "content": query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def add_tool_result(self, tool_name: str, args: dict, result: str) -> None:
        """Record a tool result to the scratchpad."""
        try:
            parsed = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            parsed = result

        self._append({
            "type": "tool_result",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "toolName": tool_name,
            "args": args,
            "result": parsed,
        })

    def add_thinking(self, thought: str) -> None:
        """Record a thinking step."""
        self._append({
            "type": "thinking",
            "content": thought,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def can_call_tool(self, tool_name: str, query: str | None = None) -> dict:
        """Check if a tool call is within soft limits.

        Returns {"allowed": True, "warning": None} or {"allowed": True, "warning": "<message>"}.
        Calls are never hard-blocked — only warned.
        """
        count = self._tool_call_counts.get(tool_name, 0)

        if count >= self._max_calls_per_tool:
            return {
                "allowed": True,
                "warning": (
                    f"{tool_name} has been called {count} times (suggested limit: "
                    f"{self._max_calls_per_tool}). Consider a different approach."
                ),
            }

        if count == self._max_calls_per_tool - 1:
            return {
                "allowed": True,
                "warning": (
                    f"{tool_name} is approaching its suggested limit "
                    f"({count + 1}/{self._max_calls_per_tool} calls)."
                ),
            }

        if query:
            previous = self._tool_queries.get(tool_name, [])
            similar = self._find_similar_query(query, previous)
            if similar:
                return {
                    "allowed": True,
                    "warning": (
                        f"{tool_name} was already called with a similar query: "
                        f'"{similar}". Consider using cached results.'
                    ),
                }

        return {"allowed": True, "warning": None}

    def record_tool_call(self, tool_name: str, query: str | None = None) -> None:
        """Record that a tool was called."""
        self._tool_call_counts[tool_name] = self._tool_call_counts.get(tool_name, 0) + 1
        if query:
            if tool_name not in self._tool_queries:
                self._tool_queries[tool_name] = []
            self._tool_queries[tool_name].append(query)

    def get_tool_results(self) -> str:
        """Format all tool results for injection into the iteration prompt."""
        entries = self._read_entries()
        tool_result_entries = [e for e in entries if e.get("type") == "tool_result"]

        parts = []
        for i, entry in enumerate(tool_result_entries):
            if i in self._cleared_tool_indices:
                parts.append(f"[Tool result #{i + 1} cleared from context]")
            else:
                tool_name = entry.get("toolName", "unknown")
                args = entry.get("args", {})
                result = entry.get("result", "")

                # Format args as k=v pairs
                args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
                result_str = self._stringify_result(result)
                parts.append(f"### {tool_name}({args_str})\n{result_str}")

        return "\n\n".join(parts)

    def format_tool_usage_for_prompt(self) -> str | None:
        """Return tool usage summary for injection into iteration prompt."""
        if not self._tool_call_counts:
            return None

        lines = ["## Tool Usage This Query\n"]
        for tool_name, count in self._tool_call_counts.items():
            if count >= self._max_calls_per_tool:
                lines.append(f"- {tool_name}: {count}/{self._max_calls_per_tool} calls (over suggested limit)")
            else:
                lines.append(f"- {tool_name}: {count}/{self._max_calls_per_tool} calls")

        lines.append(
            "\nNote: If a tool isn't returning useful results after several attempts, "
            "consider trying a different tool/approach."
        )
        return "\n".join(lines)

    def clear_oldest_tool_results(self, keep_count: int) -> int:
        """Clear oldest tool results from context (in-memory only).

        Returns count of entries cleared.
        """
        entries = self._read_entries()
        tool_result_entries = [
            (i, e) for i, e in enumerate(
                e for e in entries if e.get("type") == "tool_result"
            )
        ]

        active = [(i, e) for i, e in enumerate(
            e for e in entries if e.get("type") == "tool_result"
        ) if i not in self._cleared_tool_indices]

        total_active = len(active)
        to_clear = max(0, total_active - keep_count)

        if to_clear == 0:
            return 0

        cleared = 0
        for i, _ in active[:to_clear]:
            self._cleared_tool_indices.add(i)
            cleared += 1

        return cleared

    def has_executed_skill(self, skill_name: str) -> bool:
        """Check if a skill has already been invoked in this session."""
        entries = self._read_entries()
        for entry in entries:
            if (
                entry.get("type") == "tool_result"
                and entry.get("toolName") == "skill"
                and isinstance(entry.get("args"), dict)
                and entry["args"].get("skill") == skill_name
            ):
                return True
        return False

    def estimate_tokens(self, system_prompt: str, query: str) -> int:
        """Rough token estimate based on character count."""
        return int(
            (len(system_prompt) + len(query) + len(self.get_tool_results())) / 3.5
        )

    # --- Private helpers ---

    def _append(self, entry: dict) -> None:
        """Append a JSON entry to the scratchpad file."""
        try:
            with open(self._filepath, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as e:
            logger.warning(f"Scratchpad write failed: {e}")

    def _read_entries(self) -> list[dict]:
        """Read all valid JSONL entries from the scratchpad file."""
        entries = []
        try:
            with open(self._filepath) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except OSError:
            pass
        return entries

    def _tokenize(self, query: str) -> set[str]:
        """Tokenize a query for similarity comparison."""
        # Remove punctuation, lowercase, split
        translator = str.maketrans("", "", string.punctuation)
        words = query.translate(translator).lower().split()
        return {w for w in words if len(w) > 2}

    def _jaccard(self, set1: set, set2: set) -> float:
        """Compute Jaccard similarity between two sets."""
        if not set1 and not set2:
            return 1.0
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0.0

    def _find_similar_query(self, query: str, previous: list[str]) -> str | None:
        """Return the first previous query with Jaccard similarity >= threshold."""
        tokens = self._tokenize(query)
        for prev in previous:
            prev_tokens = self._tokenize(prev)
            if self._jaccard(tokens, prev_tokens) >= self._similarity_threshold:
                return prev
        return None

    def _stringify_result(self, result) -> str:
        """Convert a result to a string for display."""
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
