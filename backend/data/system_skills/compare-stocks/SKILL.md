---
name: compare-stocks
description: Side-by-side comparison of two or more stocks. Use when user wants to compare stocks, decide between investments, or evaluate alternatives.
---

## Overview
Compare stocks across key metrics to help the user make informed decisions.

## Process

1. **Identify Stocks:**
   - Ask user which stocks to compare if not specified
   - Recommend 2-4 stocks for meaningful comparison

2. **Gather Data for Each:**
   - Use get_quote for current price and performance
   - Use get_price_history for trend comparison
   - Use get_financial_ratios for valuation comparison

3. **Comparison Table:**
   Present a clear comparison across:
   - Current price and daily change
   - 6-month performance (from price history)
   - Valuation: P/E, P/B, P/S ratios
   - MA200 indicator
   - Volume (liquidity indicator)

4. **Analysis:**
   - Which looks more attractively valued?
   - Which has stronger momentum?
   - Risk comparison
   - Summary recommendation (without specific buy/sell advice)

## Guidelines
- Use a table format for easy comparison
- Highlight the "winner" in each category
- Note important caveats (different sectors, market caps, etc.)
