---
name: watchlist-scan
description: Quick scan of a watchlist for opportunities and risks. Use when user wants a quick update on their watchlist or asks "anything interesting happening?"
---

## Overview
Fast scan of a watchlist to surface what matters right now.

## Process

1. **Get Data:**
   - Ask which watchlist (or use default/first)
   - Use get_watchlist_items to get all stocks with current quotes

2. **Surface What Matters:**
   - Big movers today (>2% up or down)
   - Stocks crossing MA200 (trend change signals)
   - Unusual volume
   - New highs/lows (from price history if needed)

3. **Quick Report:**
   Format as a quick-scan briefing:
   - Highlights (positive signals)
   - Alerts (concerning signals)
   - Stable (business as usual)

4. **Follow-up:**
   - Ask if user wants deeper analysis on any flagged stock
   - Offer to research specific stocks that caught attention

## Guidelines
- Speed over depth — this is a quick scan
- Only flag things that are actually noteworthy
- Don't list every stock — focus on outliers
- Use emoji sparingly but effectively for visual scanning
