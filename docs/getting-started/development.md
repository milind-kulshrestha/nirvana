# Development Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+ (for local development)

### Full Stack Setup

1. **Start Backend + Database:**
```bash
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose logs -f backend
```

2. **Start Frontend:**
```bash
cd frontend
npm install
npm run dev
```

3. **Access Application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Development Workflows

### Backend Development

**Docker Compose (Recommended):**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart after code changes
docker-compose restart backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Access database
docker-compose exec db psql -U user -d watchlist

# Run tests
docker-compose exec backend pytest

# Stop services
docker-compose down
```

**Local Development:**
```bash
cd backend

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (separate terminal)
docker-compose up -d db

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Lint code
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Operations

**Create Migration:**
```bash
cd backend
alembic revision --autogenerate -m "description of change"
```

**Apply Migrations:**
```bash
alembic upgrade head
```

**Rollback Migration:**
```bash
alembic downgrade -1
```

**Reset Database:**
```bash
docker-compose down -v  # Removes volumes
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## Testing

### Backend Tests

```bash
# Using Docker
docker-compose exec backend pytest

# Local
cd backend
pytest

# With coverage
pytest --cov=app

# Specific test
pytest tests/test_auth.py
```

### Frontend Tests
*Not implemented yet*

## Environment Variables

### Backend (.env)

Create `backend/.env`:
```bash
DEBUG=true
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/watchlist
CORS_ORIGINS=http://localhost:5173
FMP_API_KEY=your-fmp-api-key  # Optional
```

**Generate SECRET_KEY:**
```bash
openssl rand -hex 32
```

### Frontend
No environment variables needed for local development.

API base URL hardcoded to `http://localhost:8000` in:
- `frontend/src/stores/authStore.js`
- Various page components

## Common Tasks

### Add New API Endpoint

1. Create route function in `backend/app/routes/`
2. Add Pydantic models for request/response
3. Register router in `backend/app/main.py` if new file
4. Test with FastAPI docs at http://localhost:8000/docs

Example:
```python
# backend/app/routes/example.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example():
    return {"message": "example"}
```

### Add New Frontend Page

1. Create page in `frontend/src/pages/`
2. Add route in `frontend/src/App.jsx`
3. Add navigation link if needed

Example:
```javascript
// frontend/src/pages/NewPage.jsx
export default function NewPage() {
  return <div>New Page</div>;
}

// frontend/src/App.jsx
<Route path="/new" element={<ProtectedRoute><NewPage /></ProtectedRoute>} />
```

### Add Database Model

1. Create model in `backend/app/models/`
2. Import in `backend/app/models/__init__.py`
3. Create migration: `alembic revision --autogenerate -m "add model"`
4. Review and apply: `alembic upgrade head`

### Add shadcn/ui Component

```bash
cd frontend
npx shadcn@latest add <component-name>
```

Components installed to `frontend/src/components/ui/`.

## Debugging

### Backend Debugging

**Enable SQL Logging:**
Set `DEBUG=true` in environment variables.

**Python Debugger:**
Add breakpoint:
```python
import pdb; pdb.set_trace()
```

**View Logs:**
```bash
docker-compose logs -f backend
```

### Frontend Debugging

**React DevTools:**
Install browser extension for component inspection.

**Console Logging:**
```javascript
console.log('Debug:', data);
```

**Network Tab:**
Inspect API requests/responses in browser DevTools.

## Troubleshooting

### Database Connection Issues

**Check PostgreSQL is running:**
```bash
docker-compose ps
# Should show db service as "Up"
```

**Test connection:**
```bash
docker-compose exec db pg_isready -U user
```

**Reset database:**
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Frontend API Connection Issues

**CORS errors:**
- Check `CORS_ORIGINS` in backend environment variables
- Ensure frontend URL matches allowed origins
- Restart backend after changes

**Session cookie not sent:**
- Ensure `credentials: 'include'` in fetch requests
- Check cookie in browser DevTools (Application tab)

### OpenBB Issues

**Rate limiting:**
- Free yfinance provider has rate limits
- Wait between requests or add FMP_API_KEY

**Symbol not found:**
- Verify symbol exists on FMP/Yahoo Finance
- Check for typos in ticker

**Configuration errors:**
- Check `~/.openbb_platform/user_settings.json`
- Ensure FMP_API_KEY is set if using FMP

### Migration Issues

**Alembic version conflicts:**
```bash
# Check current version
alembic current

# View history
alembic history

# Stamp to specific version
alembic stamp head
```

**Auto-generation missed changes:**
Manually edit migration file in `backend/alembic/versions/`.

## Code Style

### Backend (Python)
- Follow PEP 8
- Use type hints where helpful
- Docstrings for functions
- FastAPI automatic validation via Pydantic

### Frontend (JavaScript)
- ESLint configuration included
- Functional components with hooks
- Descriptive variable names
- Extract reusable components

## Git Workflow

**Recommended:**
```bash
# Create feature branch
git checkout -b feature/name

# Make changes and commit
git add .
git commit -m "description"

# Push to remote
git push origin feature/name

# Create pull request
```

## Performance Tips

### Backend
- Use database indexes for frequent queries
- Implement caching for expensive operations
- Batch database queries when possible
- Profile with DEBUG=true to see SQL queries

### Frontend
- Use React DevTools Profiler
- Memoize expensive calculations
- Implement pagination for large lists
- Lazy load routes if app grows

## Security Notes

### Development vs Production

**Development:**
- DEBUG=true
- Secure cookie flag disabled
- CORS allows localhost
- Weak SECRET_KEY acceptable

**Production:**
- DEBUG=false
- Secure cookie flag enabled (HTTPS)
- CORS restricted to production domain
- Strong SECRET_KEY (32+ random bytes)
- Environment variables from secrets manager
- Rate limiting on API endpoints
- Input validation and sanitization
