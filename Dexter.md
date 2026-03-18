# Dexter

> An autonomous agent for deep financial research

- **GitHub**: https://github.com/virattt/dexter
- **Stars**: 17,300+ | **Forks**: 2,100+
- **Language**: TypeScript (Bun runtime)
- **Status**: Active (last push March 2026)
- **License**: MIT
- **Researched**: 2026-03-07

---

## ⚠️ Critical Adoption Blocker: TypeScript-Only

**Dexter is not a Python framework.** It is built entirely in TypeScript using the Bun runtime. There is no Python SDK, no Python port, and no Python-compatible API surface. If your project requires Python implementation, you cannot use Dexter directly.

**Options if you still want the patterns:**
1. Port the agent loop to Python manually (feasible — the patterns are clean)
2. Run Dexter as a sidecar process and call it via CLI subprocess from Python
3. Use the architectural patterns from Dexter and implement them in Python with LangChain or the Anthropic SDK

---

## Overview

Dexter is a CLI-based autonomous financial research agent. Think Claude Code, but purpose-built for financial analysis. It takes complex financial questions, decomposes them into structured research tasks, executes them using real-time financial data APIs and web search, self-validates, and produces data-backed answers.

**Key capabilities:**
- Autonomous task planning and execution
- Self-validation and iterative refinement
- Real-time financial data (income statements, balance sheets, SEC filings, prices)
- Web search and browser-based scraping
- Skills system for reusable domain workflows (DCF valuation, etc.)
- Multi-provider LLM support (OpenAI, Anthropic, Google, xAI, OpenRouter, Ollama)
- WhatsApp gateway for mobile access

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    CLI (Ink/React)                   │
│               src/cli.tsx, src/index.tsx             │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                   Agent Core                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  agent.ts   │  │  prompts.ts  │  │  types.ts  │  │
│  │ (main loop) │  │(sys prompt)  │  │  (events)  │  │
│  └──────┬──────┘  └──────────────┘  └────────────┘  │
│         │                                            │
│  ┌──────▼──────┐  ┌──────────────┐                  │
│  │tool-executor│  │  scratchpad  │                   │
│  │  .ts        │  │  .ts         │                   │
│  └─────────────┘  └──────────────┘                  │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              LLM Abstraction (model/llm.ts)          │
│  OpenAI │ Anthropic │ Google │ xAI │ OpenRouter      │
│  Ollama │ DeepSeek │ Moonshot                        │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                   Tool Registry                      │
│  financial_search │ financial_metrics │ read_filings │
│  web_search │ browser │ web_fetch                    │
│  read_file │ write_file │ edit_file                  │
│  skill │ heartbeat │ x_search                        │
└─────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | File | Role |
|-----------|------|------|
| Agent loop | `src/agent/agent.ts` | Orchestrates the iterative tool-calling loop |
| System prompt | `src/agent/prompts.ts` | Builds context-rich system prompt dynamically |
| Scratchpad | `src/agent/scratchpad.ts` | Append-only JSONL log of all tool calls and thinking |
| Tool executor | `src/agent/tool-executor.ts` | Dispatches tools, streams events, handles approval |
| LLM layer | `src/model/llm.ts` | Multi-provider abstraction via LangChain |
| Tool registry | `src/tools/registry.ts` | Conditional tool loading based on env vars |
| Skills system | `src/skills/` | SKILL.md-based reusable domain workflows |
| Events | `src/agent/types.ts` | Typed streaming event system for real-time UI |

---

## LLM Loop Orchestration (Deep Dive)

The agent loop follows an **iterative tool-calling** pattern with Anthropic-style context management:

```
1. Build system prompt (static, cached)
2. Build initial user prompt (query + optional history)
   ▼
3. LOOP (max 10 iterations):
   a. Call LLM with current prompt + tools bound
   b. If response has no tool calls → emit final answer, DONE
   c. If response has tool calls:
      - Execute each tool (streaming events per tool)
      - Add full results to Scratchpad
      - Check context threshold
      - If over threshold → clear oldest tool results from context
      - Build new iteration prompt (query + scratchpad.getToolResults())
      - Continue loop
4. If max iterations hit → return partial answer with notice
```

**Key design decisions:**
- **Full context, not summarized**: Tool results are kept verbatim in context (Anthropic-style). No inline LLM summarization of tool outputs.
- **Threshold-based context clearing**: When estimated tokens exceed `CONTEXT_THRESHOLD`, oldest tool results are removed from the iteration prompt (but NOT from the JSONL log). Keeps most recent `KEEP_TOOL_USES` results.
- **Overflow retry**: On actual context overflow errors, retries up to `MAX_OVERFLOW_RETRIES=2` times with progressively fewer kept tool results.
- **Generator-based streaming**: The `run()` method is an `AsyncGenerator<AgentEvent>` — every step emits typed events for real-time UI consumption.
- **Separate final answer call**: When the LLM produces a direct response (no tool calls), that IS the final answer. No separate "synthesis" call.

**Loop limits:**
- Default max iterations: `10`
- Max context overflow retries: `2`
- Tool soft limit: `3` calls per tool per query (warning, never blocks)

---

## Prompt Architecture (Deep Dive)

### System Prompt Structure

Built dynamically by `buildSystemPrompt()` in `src/agent/prompts.ts`:

```
You are Dexter, a [channel-specific label] assistant with access to research tools.
Current date: [dynamic]
[channel preamble]

## Available Tools
[rich tool descriptions injected per-tool]

## Tool Usage Policy
[when/how to use each tool, batching hints]

## Available Skills
[skill metadata: name + description per skill]

## Skill Usage Policy
[invoke immediately when relevant, once per query]

## Heartbeat
[heartbeat management instructions]

## Behavior
[channel-specific behavior bullets]

## Identity (if SOUL.md exists)
[full SOUL.md content — philosophy, values, investing framework]

## Response Format
[channel-specific format: CLI vs WhatsApp vs default]

## Tables
[strict table format rules for box rendering]
```

**Prompt caching:** For Anthropic models, the system prompt uses `cache_control: { type: 'ephemeral' }` — saves ~90% on input token costs for repeated queries.

### SOUL.md Identity System

Dexter's "personality" is defined in `SOUL.md`, a markdown document describing the agent's values, investing philosophy (Buffett + Munger), and research methodology. This is injected verbatim into the system prompt under `## Identity`.

**User override**: Users can place a custom `~/.dexter/SOUL.md` to replace the default identity. This makes Dexter's persona completely configurable without touching code.

### Iteration Prompt Structure

After each tool execution round, `buildIterationPrompt()` builds:

```
Query: [original user query]

Data retrieved from tool calls:
### tool_name(arg1=val1, arg2=val2)
[full tool result text]

### tool_name2(...)
[full tool result]

## Tool Usage This Query
- financial_search: 2/3 calls
- web_search: 1/3 calls
Note: If a tool isn't returning useful results after several attempts...

Continue working toward answering the query. When you have gathered sufficient
data to answer, write your complete answer directly and do not call more tools...
```

The iteration prompt is reconstructed fresh each cycle from the scratchpad.

### Tool Descriptions as Prompt Engineering

Each tool has a rich **description** (in `src/tools/descriptions/`) that gets injected into the system prompt under `## Available Tools`. These descriptions are more than docstrings — they include:
- When to use vs. when NOT to use
- How to batch queries efficiently
- Output format expectations
- Delegation patterns (e.g., `financial_search` internally delegates to sub-tools)

---

## Skills System (Deep Dive)

Skills are **reusable domain workflows** defined as `SKILL.md` files with YAML frontmatter + markdown body.

### Discovery Hierarchy

```
Priority (later overrides earlier):
1. src/skills/            ← builtin skills
2. ~/.dexter/skills/      ← user-global skills
3. ./.dexter/skills/      ← project-specific skills
```

### Skill File Format

```markdown
---
name: dcf-valuation
description: Performs DCF analysis... [triggers: "fair value", "intrinsic value", "DCF"]
---

# Skill Name

## Step 1: ...
Call financial_search with these queries:
...

## Step 2: ...
```

### How Skills Are Invoked

1. Skill metadata (name + description only) is injected into the system prompt
2. When a query matches, LLM calls the `skill` tool with `{ skill: "dcf-valuation" }`
3. `tool-executor.ts` deduplicates (each skill runs once per query)
4. The skill tool loads the full `SKILL.md` instructions and returns them to the LLM
5. LLM follows the step-by-step workflow, calling other tools as instructed

**Built-in skills:**
- `dcf-valuation` — Full 8-step DCF with sensitivity analysis, WACC calculation, validation checks
- `x-research` — (inferred from directory listing)

---

## LLM Provider Layer

Multi-provider support via LangChain abstractions:

| Provider | Model prefix | Auth env var |
|----------|-------------|--------------|
| OpenAI (default) | `gpt-` | `OPENAI_API_KEY` |
| Anthropic | `claude-` | `ANTHROPIC_API_KEY` |
| Google | `gemini-` | `GOOGLE_API_KEY` |
| xAI (Grok) | `grok-` | `XAI_API_KEY` |
| OpenRouter | `openrouter:` | `OPENROUTER_API_KEY` |
| DeepSeek | `deepseek-` | `DEEPSEEK_API_KEY` |
| Moonshot | `moonshot-` | `MOONSHOT_API_KEY` |
| Ollama | `ollama:` | `OLLAMA_BASE_URL` |

Default model: `gpt-5.4`. Each provider has a "fast model" variant for lightweight tasks.

Provider resolution is prefix-based (`resolveProvider(modelName)` in `src/providers.ts`).

---

## Scratchpad Pattern

The `Scratchpad` class is one of the most interesting architectural decisions:

- **Append-only JSONL file** persisted to `.dexter/scratchpad/TIMESTAMP_HASH.jsonl`
- Stores three entry types: `init` (query), `tool_result`, `thinking`
- **In-memory context clearing** — cleared entries are tracked by index; the file is never modified
- **Tool call counting** with Jaccard similarity detection for near-duplicate query prevention
- Tool limits are soft (warnings only, never block)
- Full results for debugging; selective results for LLM context

---

## Tool Ecosystem

### Financial Tools (core)
- `financial_search` — Primary dispatcher; handles prices, financials, metrics, filings, news headlines internally
- `financial_metrics` — Direct metric lookups (revenue, market cap, etc.)
- `read_filings` — SEC 10-K, 10-Q, 8-K reader

**Data source**: financialdatasets.ai API (AAPL, NVDA, MSFT free; others require paid key)

### Web Tools
- `web_search` — Exa (preferred) → Perplexity → Tavily fallback
- `web_fetch` — Direct URL fetch
- `browser` — Playwright-based JavaScript rendering and navigation

### Filesystem Tools
- `read_file`, `write_file`, `edit_file` — Local file access
- `write_file` and `edit_file` require explicit user approval per call

### Other
- `heartbeat` — Scheduled monitoring via `~/.dexter/HEARTBEAT.md`
- `skill` — Invoke registered SKILL.md workflows
- `x_search` — X/Twitter search (requires `X_BEARER_TOKEN`)

---

## Key Design Patterns Worth Porting to Python

If you're implementing these patterns in Python, the highest-value things to adapt:

1. **Scratchpad as single source of truth** — JSONL append-only log decoupled from context management. Context clearing is in-memory; persistence is file-based.

2. **Rich tool descriptions in system prompt** — Don't just bind tools; inject detailed prose descriptions explaining when/how/when-not-to-use each tool. This dramatically improves tool selection.

3. **Iteration prompt = query + full scratchpad results** — Rebuild the user message each cycle from scratch. No conversation history in the traditional sense; the scratchpad IS the context.

4. **SOUL.md identity injection** — Separating agent identity/philosophy from tool/behavior prompts. Makes persona swappable without code changes.

5. **Skills as markdown workflows** — YAML frontmatter (name, description for prompt) + markdown body (detailed instructions returned to LLM). Discoverable, overridable, zero code per skill.

6. **Soft tool limits with prompt injection** — Track tool call counts and inject usage status into the iteration prompt as a guidance section. LLM decides when to stop; no hard blocks.

7. **Generator-based streaming events** — Every step yields typed events. Decouples agent execution from UI rendering completely.

---

## Python Equivalent Stack

To replicate Dexter patterns in Python:

| Dexter (TypeScript) | Python equivalent |
|---------------------|-------------------|
| LangChain JS | `langchain` / `anthropic` SDK directly |
| Bun runtime | uv / standard Python |
| Ink (CLI) | `rich` library |
| Tool binding | `anthropic` tool_use or `langchain` tools |
| JSONL scratchpad | Standard `jsonlines` writes |
| Skills | Same `SKILL.md` pattern, parsed with `frontmatter` lib |

---

## Trade-offs

### Strengths
- Clean, readable agent loop architecture — easy to understand and port
- Strong prompt engineering (rich tool descriptions, SOUL.md, iteration hints)
- Scratchpad pattern is elegant for debugging and context management
- Skills system is simple and extensible — no code required for new workflows
- Multi-LLM from day one
- Active development, high community traction (17k+ stars in ~5 months)

### Weaknesses
- **TypeScript/Bun only** — no Python support
- Financial-domain focused — many tools are domain-specific
- No built-in task persistence across sessions (session memory only)
- financialdatasets.ai dependency for financial data (paid API for most tickers)
- No multi-agent orchestration — single agent loop only

### Adoption Decision

| Use case | Recommendation |
|----------|---------------|
| Use Dexter as-is in a Python project | ❌ Not possible |
| Run Dexter as a subprocess from Python | ⚠️ Possible but adds Bun dep and complexity |
| Study and port Dexter's patterns to Python | ✅ High value — architecture is clean and portable |
| Use Dexter for financial research standalone | ✅ Excellent for this purpose |

---

## Setup (if using TypeScript)

```bash
# Prerequisites: Bun v1.0+
git clone https://github.com/virattt/dexter.git && cd dexter
bun install
cp env.example .env
# Edit .env: add OPENAI_API_KEY + FINANCIAL_DATASETS_API_KEY
bun start
```

**Minimum viable**: Only `OPENAI_API_KEY` required (AAPL, NVDA, MSFT are free with financialdatasets.ai).

---

## Sources

- https://github.com/virattt/dexter — Main repository
- `src/agent/agent.ts` — Agent loop implementation
- `src/agent/prompts.ts` — Prompt construction
- `src/agent/scratchpad.ts` — Scratchpad pattern
- `src/agent/tool-executor.ts` — Tool execution and streaming
- `src/model/llm.ts` — LLM provider abstraction
- `src/tools/registry.ts` — Tool registry
- `src/skills/registry.ts` — Skills discovery
- `src/skills/dcf/SKILL.md` — DCF valuation skill example
- `AGENTS.md` — Repository architecture guide
- `SOUL.md` — Agent identity document
