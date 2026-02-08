# OpenBB Python Library Reference

Comprehensive reference for the OpenBB Platform Python library used in this project.

## Installation

```bash
pip install openbb
```

## Current Usage in Project

This project uses OpenBB SDK with the FMP (Financial Modeling Prep) provider for market data. See `backend/app/lib/openbb.py` for implementation.

### Our Custom Functions

- `get_quote(symbol)` - Get real-time quote data
- `get_ma_200(symbol)` - Get 200-day moving average
- `get_history(symbol, start_date, end_date)` - Get historical price data

## OpenBB Python API Reference

### Stock Quote Data

Get real-time and historical stock quotes.

```python
from openbb import obb

# Basic quote
quote = obb.equity.price.quote(symbol="AAPL", provider="fmp")

# Multiple symbols
quotes = obb.equity.price.quote(symbol=["AAPL", "MSFT"], provider="fmp")
```

**Response Fields:**
- `symbol` - Stock ticker symbol
- `name` - Company name
- `price` - Last price
- `change` - Price change
- `percent_change` - Percentage change
- `volume` - Trading volume
- `open` - Opening price
- `high` - Day high
- `low` - Day low
- `previous_close` - Previous closing price
- `market_cap` - Market capitalization
- `pe_ratio` - Price-to-earnings ratio
- `dividend_yield` - Dividend yield

### Historical Price Data

Get historical OHLCV (Open, High, Low, Close, Volume) data.

```python
from openbb import obb

# Basic historical data
data = obb.equity.price.historical(
    symbol="AAPL",
    provider="fmp"
)

# With date range
data = obb.equity.price.historical(
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31",
    provider="fmp"
)

# Convert to DataFrame
df = data.to_df()
```

**Supported Intervals:**
- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `30m` - 30 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day (default)
- `1W` - 1 week
- `1M` - 1 month

**Response Fields:**
- `date` - Date/timestamp
- `open` - Opening price
- `high` - High price
- `low` - Low price
- `close` - Closing price
- `volume` - Trading volume
- `vwap` - Volume Weighted Average Price
- `adj_close` - Adjusted closing price
- `adj_open` - Adjusted opening price
- `adj_high` - Adjusted high price
- `adj_low` - Adjusted low price
- `split_ratio` - Stock split ratio
- `dividend` - Dividend amount

### Technical Indicators

#### Simple Moving Average (SMA)

```python
from openbb import obb

# Get historical data first
stock_data = obb.equity.price.historical(
    symbol='AAPL',
    start_date='2023-01-01',
    provider='fmp'
)

# Calculate SMA
sma_data = obb.technical.sma(
    data=stock_data.results,
    target='close',
    length=200,  # 200-day SMA
    offset=0
)
```

#### Exponential Moving Average (EMA)

```python
# Calculate EMA
ema_data = obb.technical.ema(
    data=stock_data.results,
    target='close',
    length=50,  # 50-day EMA
    offset=0
)
```

#### Weighted Moving Average (WMA)

```python
# Calculate WMA
wma_data = obb.technical.wma(
    data=stock_data.results,
    target='close',
    length=200,  # 200-day WMA
    offset=0
)
```

**Common Parameters:**
- `data` - List of data points (from historical query)
- `target` - Column to calculate on (default: 'close')
- `index` - Index column name (default: 'date')
- `length` - Period for calculation (e.g., 50, 200)
- `offset` - Offset value (default: 0)

#### MACD (Moving Average Convergence Divergence)

```python
macd_data = obb.technical.macd(
    data=stock_data.results,
    target='close',
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

## Available Providers

### FMP (Financial Modeling Prep)
- **Current provider** - Used in this project
- Real-time and historical data
- Technical indicators
- Requires API key

### Yahoo Finance (yfinance)
- Free, no API key required
- Good for historical data
- May have rate limits

```python
data = obb.equity.price.historical(
    symbol="AAPL",
    provider="yfinance"
)
```

### Polygon
- High-quality data
- Real-time and historical
- Requires API key

### Intrinio
- Professional-grade data
- Requires API key and subscription

## REST API

OpenBB also provides a REST API endpoint structure:

```
GET /equity/price/quote
GET /equity/price/historical
GET /technical/sma
GET /technical/ema
GET /technical/wma
GET /technical/macd
```

## Error Handling

```python
from openbb import obb

try:
    quote = obb.equity.price.quote(symbol="AAPL", provider="fmp")
    if quote.results:
        print(quote.results[0])
    else:
        print("No data returned")
except Exception as e:
    print(f"Error fetching quote: {e}")
```

## Data Conversion

```python
# To DataFrame
df = data.to_df()

# To dictionary
dict_data = data.to_dict()

# To JSON
json_data = data.to_json()
```

## Example: Complete Workflow

```python
from openbb import obb
from datetime import datetime, timedelta

# 1. Get current quote
quote = obb.equity.price.quote(symbol="AAPL", provider="fmp")
current_price = quote.results[0].price

# 2. Get historical data (last 200 days for MA calculation)
end_date = datetime.now()
start_date = end_date - timedelta(days=300)

historical = obb.equity.price.historical(
    symbol="AAPL",
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
    provider="fmp"
)

# 3. Calculate 200-day moving average
ma_200 = obb.technical.sma(
    data=historical.results,
    target='close',
    length=200
)

# 4. Get most recent MA value
latest_ma = ma_200.results[-1].sma

# 5. Compare price to MA
if current_price > latest_ma:
    print(f"Price ${current_price} is above 200-day MA ${latest_ma}")
else:
    print(f"Price ${current_price} is below 200-day MA ${latest_ma}")
```

## Configuration

### API Key Setup

For FMP provider, set the API key in environment variables or docker-compose.yml:

```yaml
environment:
  - OPENBB_FMP_API_KEY=your_api_key_here
```

### Provider Selection

```python
# Set default provider
obb.user.preferences.provider = "fmp"

# Or specify per query
data = obb.equity.price.historical(symbol="AAPL", provider="fmp")
```

## Performance Tips

1. **Cache historical data** - Don't fetch repeatedly
2. **Use appropriate date ranges** - Only fetch what you need
3. **Batch requests** - Use multiple symbols when supported
4. **Handle rate limits** - Add delays between requests if needed
5. **Use DataFrames** - Convert to pandas for analysis

## Common Patterns

### Check if Price is Above/Below MA

```python
def is_above_ma_200(symbol):
    """Check if current price is above 200-day MA"""
    # Get historical data (300 days to ensure 200 valid points)
    historical = obb.equity.price.historical(
        symbol=symbol,
        provider='fmp'
    )

    # Calculate 200-day SMA
    ma = obb.technical.sma(
        data=historical.results,
        target='close',
        length=200
    )

    # Get current price
    quote = obb.equity.price.quote(symbol=symbol, provider='fmp')

    return quote.results[0].price > ma.results[-1].sma
```

### Get Multiple Stocks Data

```python
def get_portfolio_quotes(symbols):
    """Get quotes for multiple symbols"""
    results = {}
    for symbol in symbols:
        try:
            quote = obb.equity.price.quote(symbol=symbol, provider='fmp')
            results[symbol] = quote.results[0]
        except Exception as e:
            results[symbol] = None
    return results
```

## Resources

- **OpenBB Documentation**: https://docs.openbb.co
- **OpenBB GitHub**: https://github.com/OpenBB-finance/OpenBB
- **FMP Documentation**: https://site.financialmodelingprep.com/developer/docs

## Version Information

- Library ID: `/docs.openbb.co/llmstxt`
- Provider: FMP (Financial Modeling Prep)
- Current Implementation: `backend/app/lib/openbb.py`
