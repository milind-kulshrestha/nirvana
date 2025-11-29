# Financial Tracker - Stock Watchlist MVP

A minimal stock watchlist tracker with live market data powered by OpenBB.

## Features

- User authentication (email/password with secure sessions)
- Create multiple watchlists
- Add stocks/crypto to watchlists by ticker symbol
- View live prices, 200-day moving average, and volume
- 6-month price history charts
- RESTful API with FastAPI

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Market Data**: OpenBB SDK (yfinance provider)
- **Auth**: Session-based with signed cookies (no JWT)

## Quick Start

### Prerequisites

- Python 3.11+ (you have 3.13.1 ✓)
- PostgreSQL 15+ (or use Docker Compose)

### Option 1: Docker Compose (Recommended)

```bash
# Start PostgreSQL + backend
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f backend
```

### Option 2: Local Development

1. **Set up virtual environment**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up database**

```bash
# Create database (if not using Docker)
createdb watchlist

# Or with psql:
psql -U postgres -c "CREATE DATABASE watchlist;"
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Run migrations**

```bash
alembic upgrade head
```

6. **Start development server**

```bash
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:

- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication

```
POST   /api/auth/register  - Register new user
POST   /api/auth/login     - Login (sets session cookie)
POST   /api/auth/logout    - Logout (clears session)
GET    /api/auth/me        - Get current user
```

### Watchlists

```
GET    /api/watchlists             - List all watchlists
POST   /api/watchlists             - Create watchlist
DELETE /api/watchlists/{id}        - Delete watchlist
POST   /api/watchlists/{id}/items  - Add stock to watchlist
DELETE /api/watchlists/{id}/items/{item_id}  - Remove stock
```

### Market Data

```
GET    /api/securities/{symbol}?include=quote,ma200,history
       - Get stock data (quote, 200-day MA, 6-month history)
```

## Example Usage

### 1. Register a user

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}' \
  -c cookies.txt
```

### 3. Create a watchlist

```bash
curl -X POST http://localhost:8000/api/watchlists \
  -H "Content-Type: application/json" \
  -d '{"name": "Tech Stocks"}' \
  -b cookies.txt
```

### 4. Add a stock

```bash
curl -X POST http://localhost:8000/api/watchlists/1/items \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}' \
  -b cookies.txt
```

### 5. Get stock data

```bash
curl http://localhost:8000/api/securities/AAPL?include=quote,ma200,history
```

## Running Tests

```bash
cd backend
pytest
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy models
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   └── watchlist_item.py
│   ├── routes/          # API endpoints
│   │   ├── auth.py
│   │   ├── watchlists.py
│   │   └── securities.py
│   ├── lib/             # Utilities
│   │   ├── auth.py      # Password & session management
│   │   ├── openbb.py    # Market data integration
│   │   └── validators.py
│   ├── config.py        # Settings
│   ├── database.py      # DB connection
│   └── main.py          # FastAPI app
├── tests/               # Tests
├── alembic/             # DB migrations
└── requirements.txt
```

## Environment Variables

See `.env.example` for all available configuration options:

- `DEBUG` - Enable debug mode
- `SECRET_KEY` - Session signing key (generate with `openssl rand -hex 32`)
- `DATABASE_URL` - PostgreSQL connection string
- `CORS_ORIGINS` - Allowed frontend origins
- `OPENBB_API_KEY` - Optional OpenBB API key for premium features

## Troubleshooting

### Database connection errors

```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep watchlist
```

### OpenBB errors

The app uses the free `yfinance` provider. If you encounter rate limits:
- Wait a few minutes between requests
- Consider getting an OpenBB API key for higher limits

### Import errors

Make sure you're in the virtual environment:

```bash
which python  # Should show venv/bin/python
```

## What's Next?

This is V1 (Week 1 backend). Next steps:

- **Week 2**: Build React frontend with Vite + TailwindCSS
- **Week 3**: Polish UI, add tests, deploy to production

## License

MIT
