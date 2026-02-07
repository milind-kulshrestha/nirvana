---
name: portfolio-review
description: Review and analyze all stocks across the user's watchlists. Use when user asks for a portfolio health check, overview, or summary.
---

## Overview
Comprehensive health check across all of the user's watchlists.

## Process

1. **Gather Data:**
   - Use get_watchlists to list all watchlists
   - For each watchlist, use get_watchlist_items to get all stocks with quotes
   - Note: This may take a moment for large portfolios

2. **Analyze Each Position:**
   - Current price and daily change
   - Position relative to MA200 (trend indicator)
   - Group into: strong performers, stable, underperforming

3. **Portfolio-Level Analysis:**
   - Overall portfolio direction (how many up vs down today)
   - Sector concentration (if identifiable from symbols)
   - Risk flags (stocks far below MA200, high volatility)

4. **Report Structure:**
   - Quick summary (1-2 sentences)
   - Winners and losers today
   - Stocks needing attention (below MA200, big drops)
   - Suggested actions (if any)

## Guidelines
- Be concise but comprehensive
- Highlight actionable insights
- Don't overwhelm with data — focus on what matters
- If portfolio is small, give more detail per stock
