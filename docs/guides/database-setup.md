# Database Setup Guide

Nirvana uses PostgreSQL with SQLAlchemy ORM and Alembic migrations.

## Database Schema Overview

```
User (1) ──────< (many) Watchlist (1) ──────< (many) WatchlistItem
```

- **CASCADE deletes** throughout the schema
- **No cached market data** - fetched on-demand from OpenBB
- **Session-based auth** - no JWT tokens stored

## Setup Instructions

### 1. Start PostgreSQL Container
```bash
docker-compose up -d db
```

### 2. Run Initial Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### 3. Verify Setup
```bash
# Access PostgreSQL directly
docker-compose exec db psql -U user -d watchlist

# List tables
\dt

# Check schema
\d users
\d watchlists  
\d watchlist_items
```

## Migration Management

### Create New Migration
```bash
# Auto-generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Create empty migration for manual changes
docker-compose exec backend alembic revision -m "description"
```

### Apply Migrations
```bash
# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Upgrade to specific revision
docker-compose exec backend alembic upgrade <revision_id>

# Downgrade one revision
docker-compose exec backend alembic downgrade -1
```

### Migration History
```bash
# Show current revision
docker-compose exec backend alembic current

# Show migration history
docker-compose exec backend alembic history

# Show pending migrations
docker-compose exec backend alembic show <revision_id>
```

## Configuration

### Environment Variables
```bash
# In docker-compose.yml
POSTGRES_DB=watchlist
POSTGRES_USER=user
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql://user:password@db:5432/watchlist
```

### Connection Settings
- **Host:** `db` (Docker service name)
- **Port:** `5432`
- **Database:** `watchlist`
- **User:** `user`
- **Password:** `password`

## Troubleshooting

### Common Issues

**Connection Refused:**
```bash
# Check if database container is running
docker-compose ps

# Check database logs
docker-compose logs db
```

**Migration Conflicts:**
```bash
# Reset to clean state (DESTRUCTIVE)
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

**Permission Errors:**
```bash
# Ensure proper ownership
docker-compose exec db chown -R postgres:postgres /var/lib/postgresql/data
```

### Data Management

**Backup Database:**
```bash
docker-compose exec db pg_dump -U user watchlist > backup.sql
```

**Restore Database:**
```bash
docker-compose exec -T db psql -U user watchlist < backup.sql
```

**Reset Database:**
```bash
docker-compose down -v  # Removes volumes
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

For detailed schema information, see [Database Architecture](../reference/architecture/database.md).
