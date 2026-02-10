#!/usr/bin/env python3
"""
OpenBB FMP Equity Data Explorer
Fetches comprehensive equity data from all FMP-supported endpoints via OpenBB Platform
and generates an interactive HTML report for dashboard analytics planning.
"""

import sys
# Remove the workspace directory from sys.path to avoid the local openbb.py shadowing the real package
_script_dir = str(__import__("pathlib").Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir and p != "."]

import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from openbb import obb

# ─── Configuration ───────────────────────────────────────────────────────────
TICKER = "AAPL"
PROVIDER = "fmp"
OUTPUT_DIR = Path(__file__).parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_PATH = OUTPUT_DIR / f"fmp_equity_report_{TICKER}_{datetime.now():%Y%m%d_%H%M%S}.html"

# ─── Data Collection ─────────────────────────────────────────────────────────

def safe_fetch(name, func, *args, **kwargs):
    """Safely call an OpenBB endpoint and return (name, df_or_None, error_or_None)."""
    try:
        result = func(*args, provider=PROVIDER, **kwargs)
        df = result.to_df()
        if df.empty:
            return name, None, "Empty result"
        return name, df, None
    except Exception as e:
        return name, None, str(e)


def fetch_all_data(ticker: str):
    """Fetch data from all 41 FMP-supported equity endpoints."""
    results = {}
    errors = {}

    calls = [
        # ── Profile & Search ──
        ("Company Profile", lambda: obb.equity.profile(ticker, provider=PROVIDER)),
        ("Historical Market Cap", lambda: obb.equity.historical_market_cap(ticker, provider=PROVIDER)),

        # ── Price ──
        ("Price: Historical (1Y Daily)", lambda: obb.equity.price.historical(
            ticker, provider=PROVIDER, start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        )),
        ("Price: Quote", lambda: obb.equity.price.quote(ticker, provider=PROVIDER)),
        ("Price: Performance", lambda: obb.equity.price.performance(ticker, provider=PROVIDER)),

        # ── Fundamentals (no limit param — triggers FMP premium gate) ──
        ("Fundamental: Income Statement (Annual)", lambda: obb.equity.fundamental.income(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Income Statement (Quarterly)", lambda: obb.equity.fundamental.income(ticker, provider=PROVIDER, period="quarter")),
        ("Fundamental: Balance Sheet (Annual)", lambda: obb.equity.fundamental.balance(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Balance Sheet (Quarterly)", lambda: obb.equity.fundamental.balance(ticker, provider=PROVIDER, period="quarter")),
        ("Fundamental: Cash Flow (Annual)", lambda: obb.equity.fundamental.cash(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Cash Flow (Quarterly)", lambda: obb.equity.fundamental.cash(ticker, provider=PROVIDER, period="quarter")),
        ("Fundamental: Income Growth", lambda: obb.equity.fundamental.income_growth(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Balance Growth", lambda: obb.equity.fundamental.balance_growth(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Cash Flow Growth", lambda: obb.equity.fundamental.cash_growth(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Key Metrics", lambda: obb.equity.fundamental.metrics(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Financial Ratios", lambda: obb.equity.fundamental.ratios(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Historical Splits", lambda: obb.equity.fundamental.historical_splits(ticker, provider=PROVIDER)),
        ("Fundamental: Management", lambda: obb.equity.fundamental.management(ticker, provider=PROVIDER)),
        ("Fundamental: Management Compensation", lambda: obb.equity.fundamental.management_compensation(ticker, provider=PROVIDER)),
        ("Fundamental: Revenue by Geography", lambda: obb.equity.fundamental.revenue_per_geography(ticker, provider=PROVIDER, period="annual")),
        ("Fundamental: Revenue by Segment", lambda: obb.equity.fundamental.revenue_per_segment(ticker, provider=PROVIDER, period="annual")),

        # ── Estimates ──
        ("Estimates: Consensus", lambda: obb.equity.estimates.consensus(ticker, provider=PROVIDER)),
        ("Estimates: Forward EPS", lambda: obb.equity.estimates.forward_eps(ticker, provider=PROVIDER)),
        ("Estimates: Forward EBITDA", lambda: obb.equity.estimates.forward_ebitda(ticker, provider=PROVIDER)),

        # ── Ownership ──
        ("Ownership: Share Statistics", lambda: obb.equity.ownership.share_statistics(ticker, provider=PROVIDER)),

        # ── Discovery (market-wide, no ticker) ──
        ("Discovery: Most Active", lambda: obb.equity.discovery.active(provider=PROVIDER)),
        ("Discovery: Top Gainers", lambda: obb.equity.discovery.gainers(provider=PROVIDER)),
        ("Discovery: Top Losers", lambda: obb.equity.discovery.losers(provider=PROVIDER)),

        # ── Compare ──
        ("Compare: Peers", lambda: obb.equity.compare.peers(ticker, provider=PROVIDER)),

        # ── Calendar (market-wide) ──
        ("Calendar: Upcoming Dividends", lambda: obb.equity.calendar.dividend(
            provider=PROVIDER, start_date=datetime.now().strftime("%Y-%m-%d"),
            end_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        )),
        ("Calendar: Upcoming Earnings", lambda: obb.equity.calendar.earnings(
            provider=PROVIDER, start_date=datetime.now().strftime("%Y-%m-%d"),
            end_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        )),
    ]

    total = len(calls)
    for i, (name, func) in enumerate(calls, 1):
        print(f"  [{i:2d}/{total}] Fetching: {name}...", end=" ", flush=True)
        try:
            result = func()
            df = result.to_df()
            if df.empty:
                errors[name] = "Empty result"
                print("⚠ empty")
            else:
                results[name] = df
                print(f"✓ ({len(df)} rows, {len(df.columns)} cols)")
        except Exception as e:
            errors[name] = str(e)
            print(f"✗ {str(e)[:80]}")

    return results, errors


# ─── HTML Report Generation ──────────────────────────────────────────────────

def df_to_html_table(df: pd.DataFrame, max_rows: int = 50, max_col_width: int = 120) -> str:
    """Convert a DataFrame to a styled HTML table."""
    df_display = df.head(max_rows).copy()

    # Truncate long string columns for display
    for col in df_display.columns:
        if df_display[col].dtype == object:
            df_display[col] = df_display[col].astype(str).str[:max_col_width]
            df_display[col] = df_display[col].where(
                df_display[col].str.len() < max_col_width,
                df_display[col] + "..."
            )

    # Format numeric columns
    for col in df_display.select_dtypes(include=["float64", "float32"]).columns:
        df_display[col] = df_display[col].apply(
            lambda x: f"{x:,.2f}" if pd.notna(x) else ""
        )

    html = df_display.to_html(
        classes="data-table",
        index=True,
        border=0,
        na_rep="—",
        escape=True,
    )
    if len(df) > max_rows:
        html += f'<p class="truncated">Showing {max_rows} of {len(df)} rows</p>'
    return html


def build_column_summary(df: pd.DataFrame) -> str:
    """Build a summary of columns with types and sample values."""
    rows = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notna().sum()
        total = len(df)
        sample = str(df[col].dropna().iloc[0])[:80] if non_null > 0 else "—"
        rows.append(f"<tr><td><code>{col}</code></td><td>{dtype}</td><td>{non_null}/{total}</td><td>{sample}</td></tr>")
    return f"""
    <table class="schema-table">
        <thead><tr><th>Column</th><th>Type</th><th>Non-Null</th><th>Sample Value</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    """


def generate_report(ticker: str, results: dict, errors: dict) -> str:
    """Generate a comprehensive HTML report."""

    # Build navigation and sections
    nav_items = []
    sections = []

    # Group results by category
    categories = {
        "Profile & Market Data": [],
        "Price Data": [],
        "Fundamental: Financial Statements": [],
        "Fundamental: Growth Metrics": [],
        "Fundamental: Key Metrics & Ratios": [],
        "Fundamental: Corporate Info": [],
        "Fundamental: Revenue Breakdown": [],
        "Estimates & Analyst Data": [],
        "Ownership": [],
        "Market Discovery": [],
        "Calendar Events": [],
        "Screener": [],
        "Earnings Transcripts": [],
    }

    category_map = {
        "Company Profile": "Profile & Market Data",
        "Historical Market Cap": "Profile & Market Data",
        "Price: Historical (1Y Daily)": "Price Data",
        "Price: Quote": "Price Data",
        "Price: Performance": "Price Data",
        "Fundamental: Income Statement (Annual)": "Fundamental: Financial Statements",
        "Fundamental: Income Statement (Quarterly)": "Fundamental: Financial Statements",
        "Fundamental: Balance Sheet (Annual)": "Fundamental: Financial Statements",
        "Fundamental: Balance Sheet (Quarterly)": "Fundamental: Financial Statements",
        "Fundamental: Cash Flow (Annual)": "Fundamental: Financial Statements",
        "Fundamental: Cash Flow (Quarterly)": "Fundamental: Financial Statements",
        "Fundamental: Income Growth": "Fundamental: Growth Metrics",
        "Fundamental: Balance Growth": "Fundamental: Growth Metrics",
        "Fundamental: Cash Flow Growth": "Fundamental: Growth Metrics",
        "Fundamental: Key Metrics": "Fundamental: Key Metrics & Ratios",
        "Fundamental: Financial Ratios": "Fundamental: Key Metrics & Ratios",
        "Fundamental: Historical Splits": "Fundamental: Corporate Info",
        "Fundamental: Management": "Fundamental: Corporate Info",
        "Fundamental: Management Compensation": "Fundamental: Corporate Info",
        "Fundamental: Revenue by Geography": "Fundamental: Revenue Breakdown",
        "Fundamental: Revenue by Segment": "Fundamental: Revenue Breakdown",
        "Estimates: Consensus": "Estimates & Analyst Data",
        "Estimates: Forward EPS": "Estimates & Analyst Data",
        "Estimates: Forward EBITDA": "Estimates & Analyst Data",
        "Ownership: Share Statistics": "Ownership",
        "Discovery: Most Active": "Market Discovery",
        "Discovery: Top Gainers": "Market Discovery",
        "Discovery: Top Losers": "Market Discovery",
        "Compare: Peers": "Profile & Market Data",
        "Calendar: Upcoming Dividends": "Calendar Events",
        "Calendar: Upcoming Earnings": "Calendar Events",
        "Calendar: IPO Calendar": "Calendar Events",
        "Calendar: Stock Splits": "Calendar Events",
        "Screener: Large Cap Tech": "Screener",
    }

    for name, df in results.items():
        cat = category_map.get(name, "Other")
        if cat in categories:
            categories[cat].append((name, df))
        else:
            categories.setdefault("Other", []).append((name, df))

    section_id = 0
    for cat_name, items in categories.items():
        if not items:
            continue
        cat_id = f"cat-{section_id}"
        nav_items.append(f'<a href="#{cat_id}" class="nav-category">{cat_name} <span class="badge">{len(items)}</span></a>')

        cat_sections = []
        for name, df in items:
            sid = f"section-{section_id}"
            section_id += 1
            nav_items.append(f'<a href="#{sid}" class="nav-item">{name}</a>')

            # Dashboard relevance notes
            dashboard_notes = get_dashboard_notes(name, df)

            cat_sections.append(f"""
            <div class="data-section" id="{sid}">
                <h3>{name}</h3>
                <div class="meta">
                    <span class="meta-item">{len(df)} rows</span>
                    <span class="meta-item">{len(df.columns)} columns</span>
                    <span class="meta-item">Provider: FMP</span>
                </div>
                {f'<div class="dashboard-notes"><strong>Dashboard Ideas:</strong> {dashboard_notes}</div>' if dashboard_notes else ''}
                <details open>
                    <summary>Schema ({len(df.columns)} fields)</summary>
                    {build_column_summary(df)}
                </details>
                <details open>
                    <summary>Data Preview</summary>
                    <div class="table-wrapper">
                        {df_to_html_table(df)}
                    </div>
                </details>
            </div>
            """)

        sections.append(f"""
        <div class="category-section" id="{cat_id}">
            <h2>{cat_name}</h2>
            {''.join(cat_sections)}
        </div>
        """)

    # Error section
    error_section = ""
    if errors:
        error_rows = "".join(
            f"<tr><td>{name}</td><td>{err[:200]}</td></tr>" for name, err in errors.items()
        )
        error_section = f"""
        <div class="category-section" id="errors">
            <h2>Endpoints with Errors / Empty Results ({len(errors)})</h2>
            <table class="data-table">
                <thead><tr><th>Endpoint</th><th>Error</th></tr></thead>
                <tbody>{error_rows}</tbody>
            </table>
        </div>
        """
        nav_items.append(f'<a href="#errors" class="nav-category nav-error">Errors <span class="badge badge-error">{len(errors)}</span></a>')

    # Summary stats
    total_endpoints = len(results) + len(errors)
    success_count = len(results)
    total_rows = sum(len(df) for df in results.values())
    total_fields = sum(len(df.columns) for df in results.values())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenBB FMP Equity Report — {ticker}</title>
<style>
    :root {{
        --bg: #0a0a0f;
        --surface: #12121a;
        --surface2: #1a1a26;
        --border: #2a2a3a;
        --text: #e4e4ef;
        --text-muted: #8888a0;
        --accent: #6366f1;
        --accent-light: #818cf8;
        --green: #22c55e;
        --red: #ef4444;
        --orange: #f59e0b;
        --blue: #3b82f6;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: var(--bg);
        color: var(--text);
        line-height: 1.6;
    }}
    .layout {{
        display: grid;
        grid-template-columns: 280px 1fr;
        min-height: 100vh;
    }}
    /* Sidebar */
    .sidebar {{
        background: var(--surface);
        border-right: 1px solid var(--border);
        padding: 24px 16px;
        position: sticky;
        top: 0;
        height: 100vh;
        overflow-y: auto;
    }}
    .sidebar h1 {{
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 4px;
        color: var(--accent-light);
    }}
    .sidebar .subtitle {{
        font-size: 12px;
        color: var(--text-muted);
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border);
    }}
    .nav-category {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 10px;
        margin-top: 8px;
        font-size: 13px;
        font-weight: 600;
        color: var(--text);
        text-decoration: none;
        border-radius: 6px;
        transition: background 0.15s;
    }}
    .nav-category:hover {{ background: var(--surface2); }}
    .nav-item {{
        display: block;
        padding: 4px 10px 4px 20px;
        font-size: 12px;
        color: var(--text-muted);
        text-decoration: none;
        border-radius: 4px;
        transition: all 0.15s;
    }}
    .nav-item:hover {{ color: var(--text); background: var(--surface2); }}
    .badge {{
        background: var(--accent);
        color: white;
        font-size: 10px;
        padding: 2px 7px;
        border-radius: 10px;
        font-weight: 600;
    }}
    .badge-error {{ background: var(--red); }}
    .nav-error {{ color: var(--red); }}

    /* Main content */
    .main {{
        padding: 32px 40px;
        max-width: 1200px;
    }}
    .header {{
        margin-bottom: 32px;
    }}
    .header h1 {{
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, var(--accent-light), var(--blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }}
    .header p {{ color: var(--text-muted); font-size: 14px; }}

    /* Stats bar */
    .stats-bar {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 36px;
    }}
    .stat-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 18px 20px;
    }}
    .stat-card .label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
    .stat-card .value {{ font-size: 28px; font-weight: 700; margin-top: 4px; }}
    .stat-card .value.green {{ color: var(--green); }}
    .stat-card .value.blue {{ color: var(--blue); }}
    .stat-card .value.orange {{ color: var(--orange); }}
    .stat-card .value.accent {{ color: var(--accent-light); }}

    /* Category sections */
    .category-section {{
        margin-bottom: 48px;
    }}
    .category-section > h2 {{
        font-size: 20px;
        font-weight: 700;
        padding-bottom: 12px;
        border-bottom: 2px solid var(--accent);
        margin-bottom: 24px;
    }}
    .data-section {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 24px;
        margin-bottom: 20px;
    }}
    .data-section h3 {{
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
    }}
    .meta {{
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
    }}
    .meta-item {{
        font-size: 12px;
        color: var(--text-muted);
        background: var(--surface2);
        padding: 3px 10px;
        border-radius: 4px;
    }}
    .dashboard-notes {{
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 13px;
        color: var(--accent-light);
    }}

    /* Tables */
    .table-wrapper {{
        overflow-x: auto;
        border-radius: 6px;
    }}
    .data-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }}
    .data-table th {{
        background: var(--surface2);
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
        color: var(--text-muted);
        border-bottom: 1px solid var(--border);
        white-space: nowrap;
    }}
    .data-table td {{
        padding: 6px 12px;
        border-bottom: 1px solid var(--border);
        white-space: nowrap;
        max-width: 300px;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .data-table tr:hover td {{ background: var(--surface2); }}
    .schema-table {{ margin-bottom: 12px; }}
    .schema-table code {{ color: var(--accent-light); font-size: 12px; }}
    .truncated {{
        font-size: 12px;
        color: var(--text-muted);
        font-style: italic;
        padding: 8px 0;
    }}

    /* Details/Summary */
    details {{
        margin-bottom: 12px;
    }}
    summary {{
        cursor: pointer;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted);
        padding: 6px 0;
        user-select: none;
    }}
    summary:hover {{ color: var(--text); }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: var(--surface); }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}
</style>
</head>
<body>
<div class="layout">
    <nav class="sidebar">
        <h1>FMP Equity Explorer</h1>
        <div class="subtitle">{ticker} &middot; Generated {datetime.now():%Y-%m-%d %H:%M}</div>
        {''.join(nav_items)}
    </nav>
    <main class="main">
        <div class="header">
            <h1>OpenBB × FMP Equity Data Report</h1>
            <p>Comprehensive data exploration for <strong>{ticker}</strong> using Financial Modeling Prep (FMP) as the data provider via OpenBB Platform v4.1</p>
        </div>
        <div class="stats-bar">
            <div class="stat-card">
                <div class="label">Endpoints Called</div>
                <div class="value accent">{total_endpoints}</div>
            </div>
            <div class="stat-card">
                <div class="label">Successful</div>
                <div class="value green">{success_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Data Rows</div>
                <div class="value blue">{total_rows:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Unique Fields</div>
                <div class="value orange">{total_fields}</div>
            </div>
        </div>
        {''.join(sections)}
        {error_section}
    </main>
</div>
</body>
</html>"""
    return html


def get_dashboard_notes(name: str, df: pd.DataFrame) -> str:
    """Return dashboard widget suggestions based on the data type."""
    notes = {
        "Company Profile": "Hero card with company name, sector, market cap, CEO, employees. Key stats row: beta, year high/low, avg volume.",
        "Historical Market Cap": "Market cap trend line chart. Compare against index or peers.",
        "Price: Historical (1Y Daily)": "Candlestick/OHLCV chart with volume bars. Moving averages overlay. Date range selector.",
        "Price: Quote": "Real-time quote card: price, change %, day range, 52-week range, volume vs avg.",
        "Price: Performance": "Performance heatmap: 1D, 5D, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y returns in colored tiles.",
        "Fundamental: Income Statement (Annual)": "Revenue & net income bar chart over time. Margin trend lines (gross, operating, net).",
        "Fundamental: Income Statement (Quarterly)": "Quarterly revenue waterfall chart. QoQ growth indicators.",
        "Fundamental: Balance Sheet (Annual)": "Assets vs liabilities stacked area chart. Debt-to-equity trend.",
        "Fundamental: Balance Sheet (Quarterly)": "Quarterly cash position trend. Working capital analysis.",
        "Fundamental: Cash Flow (Annual)": "Operating/investing/financing cash flow stacked bar chart. Free cash flow trend line.",
        "Fundamental: Cash Flow (Quarterly)": "Quarterly FCF trend. CapEx as % of revenue.",
        "Fundamental: Income Growth": "Growth rate sparklines for revenue, net income, EPS. Color-coded positive/negative.",
        "Fundamental: Balance Growth": "Asset & equity growth rate comparison chart.",
        "Fundamental: Cash Flow Growth": "FCF growth trend. Operating cash flow growth vs revenue growth.",
        "Fundamental: Key Metrics": "KPI dashboard: PE, PB, EV/EBITDA, ROE, ROA, debt ratios. Sparkline trends.",
        "Fundamental: Financial Ratios": "Ratio comparison radar chart. Profitability, liquidity, leverage gauges.",
        "Fundamental: Dividends": "Dividend history timeline. Yield trend chart. Payout ratio analysis.",
        "Fundamental: Employee Count": "Employee count trend line. Revenue per employee metric.",
        "Fundamental: Historical EPS": "EPS bar chart with actual vs estimated. Beat/miss indicators.",
        "Fundamental: Historical Splits": "Split timeline on price chart. Adjustment factor display.",
        "Fundamental: Management": "Executive team cards with titles. Org chart visualization.",
        "Fundamental: Management Compensation": "Compensation breakdown: salary, bonus, stock awards. Total comp trend.",
        "Fundamental: Revenue by Geography": "Geographic revenue pie/donut chart. World map heatmap.",
        "Fundamental: Revenue by Segment": "Segment revenue treemap or stacked bar chart. Segment growth comparison.",
        "Fundamental: Earnings Call Transcript (Latest)": "Searchable transcript viewer. Sentiment analysis highlights. Key topics extraction.",
        "Estimates: Consensus": "Consensus rating badge (buy/hold/sell). Target price range indicator.",
        "Estimates: Price Target": "Price target scatter plot by analyst. Current price vs consensus target gauge.",
        "Estimates: Historical": "Historical estimates vs actuals comparison chart. Revision trend.",
        "Estimates: Forward EPS": "Forward EPS trend with confidence bands. Fiscal year comparison.",
        "Estimates: Forward EBITDA": "Forward EBITDA projections bar chart.",
        "Estimates: Forward Sales": "Forward revenue projections with growth rate annotations.",
        "Estimates: Forward PE": "Forward PE trend vs historical PE. Sector comparison.",
        "Ownership: Insider Trading": "Insider transaction timeline. Buy vs sell volume chart. Alert on large transactions.",
        "Ownership: Institutional": "Top holders bar chart. Ownership concentration pie chart. Changes quarter-over-quarter.",
        "Ownership: Major Holders": "Major holder cards with % ownership. Institutional vs insider vs public breakdown.",
        "Ownership: Share Statistics": "Float analysis: shares outstanding, float, short interest. Short ratio gauge.",
        "Discovery: Most Active": "Market movers table with volume bars. Sortable by volume, change %.",
        "Discovery: Top Gainers": "Top gainers leaderboard with green change indicators. Sector distribution.",
        "Discovery: Top Losers": "Top losers leaderboard with red change indicators. Sector distribution.",
        "Compare: Peers": "Peer comparison table. Multi-metric radar chart for competitive analysis.",
        "Calendar: Upcoming Dividends": "Dividend calendar widget. Ex-date countdown timers.",
        "Calendar: Upcoming Earnings": "Earnings calendar with expected EPS. Countdown to next report.",
        "Calendar: IPO Calendar": "IPO pipeline timeline. Expected valuation ranges.",
        "Calendar: Stock Splits": "Split calendar with ratio display.",
        "Screener: Large Cap Tech": "Screener results grid with mini sparklines. Filter/sort controls.",
    }
    return notes.get(name, "")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  OpenBB FMP Equity Data Explorer")
    print(f"  Ticker: {TICKER} | Provider: {PROVIDER}")
    print(f"{'='*60}")
    print()

    print("Fetching data from FMP-supported endpoints...")
    print()
    results, errors = fetch_all_data(TICKER)

    print()
    print(f"Results: {len(results)} successful, {len(errors)} errors/empty")
    print()

    print("Generating HTML report...")
    html = generate_report(TICKER, results, errors)
    REPORT_PATH.write_text(html)
    print(f"Report saved to: {REPORT_PATH}")
    print(f"Open in browser: file://{REPORT_PATH.resolve()}")
