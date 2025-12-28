# Database Architecture

## PostgreSQL Schema

### Technology
- PostgreSQL 15
- SQLAlchemy ORM
- Alembic migrations

### Entity Relationship Diagram

```
User (1) ──────< (many) Watchlist (1) ──────< (many) WatchlistItem
```

## Tables

### users
```sql
id              SERIAL PRIMARY KEY
email           VARCHAR UNIQUE NOT NULL
password_hash   VARCHAR NOT NULL
created_at      TIMESTAMP DEFAULT NOW()

INDEX idx_users_email ON users(email)
```

**Relationships:**
- One user can have many watchlists

**Security:**
- Passwords hashed with bcrypt (12 rounds)
- Email stored lowercase and trimmed
- Email uniqueness enforced at DB level

### watchlists
```sql
id          SERIAL PRIMARY KEY
name        VARCHAR NOT NULL
user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
created_at  TIMESTAMP DEFAULT NOW()
```

**Relationships:**
- Belongs to one user
- Has many watchlist items

**Constraints:**
- CASCADE delete: deleting user deletes all their watchlists

### watchlist_items
```sql
id              SERIAL PRIMARY KEY
watchlist_id    INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE
symbol          VARCHAR NOT NULL
added_at        TIMESTAMP DEFAULT NOW()
```

**Relationships:**
- Belongs to one watchlist

**Constraints:**
- CASCADE delete: deleting watchlist deletes all its items
- Symbol is ticker (e.g., "AAPL", "TSLA")

**Notes:**
- No cached market data stored
- Market data fetched on-demand via OpenBB API
- Duplicate symbols allowed (no unique constraint)

## SQLAlchemy Models

### User Model (`backend/app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
```

### Watchlist Model (`backend/app/models/watchlist.py`)
```python
class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
```

### WatchlistItem Model (`backend/app/models/watchlist_item.py`)
```python
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    symbol = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    watchlist = relationship("Watchlist", back_populates="items")
```

## Database Configuration

### Connection (`backend/app/database.py`)
```python
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG  # Log SQL in debug mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Connection String Format
```
postgresql://user:password@host:port/database
```

Default (Docker): `postgresql://user:password@db:5432/watchlist`

## Migrations (Alembic)

### Configuration
- Config file: `backend/alembic.ini`
- Env file: `backend/alembic/env.py`
- Versions: `backend/alembic/versions/`

### Commands

**Create Migration:**
```bash
cd backend
alembic revision --autogenerate -m "description"
```

**Apply Migrations:**
```bash
alembic upgrade head
```

**Rollback:**
```bash
alembic downgrade -1        # Down one version
alembic downgrade <revision> # Down to specific version
```

**View History:**
```bash
alembic history             # Show all migrations
alembic current             # Show current version
```

### Migration Workflow

1. Modify SQLAlchemy models
2. Generate migration: `alembic revision --autogenerate -m "add xyz"`
3. Review generated migration in `alembic/versions/`
4. Apply migration: `alembic upgrade head`
5. Test changes

**Important:**
- Always review auto-generated migrations
- Alembic may miss complex changes (e.g., data transformations)
- Add custom operations if needed

## Docker Setup

### docker-compose.yml
```yaml
db:
  image: postgres:15
  environment:
    POSTGRES_DB: watchlist
    POSTGRES_USER: user
    POSTGRES_PASSWORD: password
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

### Accessing Database

**Via Docker:**
```bash
docker-compose exec db psql -U user -d watchlist
```

**Locally:**
```bash
psql -h localhost -U user -d watchlist
```

## Query Patterns

### Get User's Watchlists
```python
watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
```

### Get Watchlist with Items
```python
watchlist = db.query(Watchlist).filter(
    Watchlist.id == watchlist_id,
    Watchlist.user_id == user_id
).first()

# Access items via relationship
items = watchlist.items
```

### Add Item to Watchlist
```python
item = WatchlistItem(watchlist_id=watchlist_id, symbol=symbol)
db.add(item)
db.commit()
```

### Delete Watchlist (cascades to items)
```python
db.delete(watchlist)
db.commit()
```

## Data Integrity

### Constraints
- Foreign key constraints enforce relationships
- CASCADE deletes prevent orphaned records
- Unique constraint on user email

### Transaction Management
- FastAPI dependency `get_db()` manages sessions
- Sessions auto-commit on success, rollback on error
- Use `db.commit()` to persist changes

### Indexes
- Primary keys automatically indexed
- User email indexed for login queries
- Add indexes for frequently queried fields if needed

## Backup and Restore

### Backup
```bash
docker-compose exec db pg_dump -U user watchlist > backup.sql
```

### Restore
```bash
docker-compose exec -T db psql -U user watchlist < backup.sql
```

## Development Notes

### Initial Setup
```bash
# Start PostgreSQL
docker-compose up -d db

# Create tables
docker-compose exec backend alembic upgrade head
```

### Reset Database
```bash
# Drop and recreate
docker-compose down -v  # Remove volumes
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Common Queries

**Count users:**
```sql
SELECT COUNT(*) FROM users;
```

**List watchlists with item counts:**
```sql
SELECT w.id, w.name, COUNT(wi.id) as item_count
FROM watchlists w
LEFT JOIN watchlist_items wi ON w.id = wi.watchlist_id
GROUP BY w.id, w.name;
```

**Find duplicate symbols in watchlist:**
```sql
SELECT symbol, COUNT(*) as count
FROM watchlist_items
WHERE watchlist_id = ?
GROUP BY symbol
HAVING COUNT(*) > 1;
```
