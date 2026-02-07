---
name: research-stock
description: Conduct comprehensive equity research following professional analysis methodology. Use when user asks to research, analyze, or evaluate a stock.
---

## Overview
Conduct comprehensive stock research following professional equity analysis principles.

## Phase 1: Clarifying Questions
Ask user to focus the research:
1. "What's your investment horizon?" (day trade / swing / long-term / learning)
2. "What do you want to understand?" (business model / financials / valuation / all)
3. "Any specific concerns or catalysts you're tracking?"

## Phase 2: Research
Use your tools to gather data across these areas:

**Current State:**
- Use get_quote to get current price, change, volume
- Note the MA200 indicator (above/below)

**Price Trend:**
- Use get_price_history for 6-month trend analysis
- Identify support/resistance levels, trend direction

**Valuation:**
- Use get_financial_ratios for P/E, P/B, P/S ratios
- Compare to sector averages (use your knowledge)
- Assess if current valuation seems reasonable

**Risk Assessment:**
- Volatility from price history
- Valuation risk (overvalued/undervalued signals)
- Market positioning

## Phase 3: Synthesis
Build investment thesis:
- Clear bull/bear case with specific data points
- 3-5 key metrics to track going forward
- Risk/reward assessment
- What would change the thesis

## Phase 4: Review
Present findings and ask: "Does this look good? Want me to add this stock to a watchlist?"
If yes, use propose_action to add to watchlist.

## Output Standards
- Objective: facts over hype, acknowledge bear case
- Actionable: clear thesis with metrics to track
- Sourced: cite specific numbers from tool results
- Balanced: equal weight to risks and opportunities
