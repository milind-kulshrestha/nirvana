# Quick Start Guide

Get Nirvana up and running in minutes.

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Git

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nirvana
   ```

2. **Start backend services**
   ```bash
   docker-compose up -d
   ```

3. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Install and start frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - API Documentation: http://localhost:8000/docs

## Common Commands

### Backend
```bash
docker-compose up -d                        # Start services
docker-compose logs -f backend              # View logs
docker-compose restart backend              # Restart after changes
docker-compose exec backend pytest          # Run tests
docker-compose exec backend alembic upgrade head  # Run migrations
alembic revision --autogenerate -m "msg"    # Create migration
```

### Frontend
```bash
cd frontend
npm run dev                                 # Dev server
npm run build                               # Production build
npm run lint                                # Lint code
```

### Database
```bash
docker-compose exec db psql -U user -d watchlist  # Access PostgreSQL
```

## Next Steps

- Read the [Development Guide](development.md) for detailed workflow
- Check [Architecture Documentation](../reference/architecture/) to understand the system
- Review [Project Status](../project/status.md) for current development state
