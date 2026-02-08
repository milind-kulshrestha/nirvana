# Database Architecture

## PostgreSQL Schema

### Technology
- PostgreSQL 15
- SQLAlchemy ORM
- Alembic migrations

### Entity Relationship Diagram

```
User (1) ──────< (many) Watchlist (1) ──────< (many) WatchlistItem
 │
 ├─────< (many) Conversation (1) ──────< (many) Message
 │
 ├─────< (many) MemoryFact
 │
 ├─────< (many) PendingAction
 │
 └─────< (many) Skill
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
- One user can have many conversations (AI chat)
- One user can have many memory facts (AI personalization)
- One user can have many pending actions (AI approvals)
- One user can have many skills (AI capabilities)

**Security:**
- Passwords hashed with bcrypt (12 rounds)
- Email stored lowercase and trimmed
- Email uniqueness enforced at DB level

**AI Agent Fields:**
- `ai_memory_enabled` - Boolean flag to enable/disable memory extraction

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

### conversations
```sql
id          SERIAL PRIMARY KEY
user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
title       VARCHAR
created_at  TIMESTAMP DEFAULT NOW()
updated_at  TIMESTAMP DEFAULT NOW()

INDEX idx_conversations_user_id ON conversations(user_id)
```

**Relationships:**
- Belongs to one user
- Has many messages

**Constraints:**
- CASCADE delete: deleting user deletes all their conversations

### messages
```sql
id                  SERIAL PRIMARY KEY
conversation_id     INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE
role                VARCHAR NOT NULL  -- 'user' or 'assistant'
content             TEXT NOT NULL
metadata            JSONB             -- tool_calls, tool_results, etc.
created_at          TIMESTAMP DEFAULT NOW()

INDEX idx_messages_conversation_id ON messages(conversation_id)
```

**Relationships:**
- Belongs to one conversation

**Constraints:**
- CASCADE delete: deleting conversation deletes all its messages
- Ordered by `created_at` ASC for chronological display

**Metadata Structure:**
```json
{
  "tool_calls": [{"id": "...", "name": "get_stock_quote", "input": {...}}],
  "tool_results": [{"tool_call_id": "...", "content": "..."}]
}
```

### memory_facts
```sql
id                      SERIAL PRIMARY KEY
user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
fact_type               VARCHAR NOT NULL  -- 'preference', 'goal', 'context'
content                 TEXT NOT NULL
source_conversation_id  INTEGER REFERENCES conversations(id) ON DELETE SET NULL
created_at              TIMESTAMP DEFAULT NOW()

INDEX idx_memory_facts_user_id ON memory_facts(user_id)
INDEX idx_memory_facts_fact_type ON memory_facts(fact_type)
```

**Relationships:**
- Belongs to one user
- Optionally linked to source conversation

**Constraints:**
- CASCADE delete on user
- SET NULL on conversation delete (preserve fact)

**Fact Types:**
- `preference` - Investment style, risk tolerance, sector preferences
- `goal` - Financial goals, time horizon, target allocations
- `context` - Account details, tax situation, constraints

### pending_actions
```sql
id                  SERIAL PRIMARY KEY
user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
conversation_id     INTEGER REFERENCES conversations(id) ON DELETE SET NULL
action_type         VARCHAR NOT NULL  -- 'add_to_watchlist', 'create_watchlist', etc.
params              JSONB NOT NULL    -- Action parameters
status              VARCHAR NOT NULL DEFAULT 'pending'  -- 'pending', 'confirmed', 'rejected'
created_at          TIMESTAMP DEFAULT NOW()

INDEX idx_pending_actions_user_id ON pending_actions(user_id)
INDEX idx_pending_actions_status ON pending_actions(status)
```

**Relationships:**
- Belongs to one user
- Optionally linked to conversation

**Constraints:**
- CASCADE delete on user
- SET NULL on conversation delete

**Action Types:**
- `add_to_watchlist` - Add stock to watchlist
- `remove_from_watchlist` - Remove stock from watchlist
- `create_watchlist` - Create new watchlist
- `delete_watchlist` - Delete watchlist

**Params Example:**
```json
{
  "watchlist_id": 1,
  "symbol": "AAPL"
}
```

### skills
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE  -- NULL for system skills
name            VARCHAR NOT NULL
description     TEXT NOT NULL
content         TEXT NOT NULL  -- Markdown skill definition
is_system       BOOLEAN NOT NULL DEFAULT FALSE
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()

INDEX idx_skills_user_id ON skills(user_id)
INDEX idx_skills_is_system ON skills(is_system)
```

**Relationships:**
- Optionally belongs to one user (system skills have NULL user_id)

**Constraints:**
- CASCADE delete on user (user skills only)
- System skills (is_system=TRUE) have NULL user_id

**System Skills:**
- research-stock
- portfolio-review
- compare-stocks
- earnings-preview
- watchlist-scan

## SQLAlchemy Models

### User Model (`backend/app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    ai_memory_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memory_facts = relationship("MemoryFact", back_populates="user", cascade="all, delete-orphan")
    pending_actions = relationship("PendingAction", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
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

### Conversation Model (`backend/app/models/conversation.py`)
```python
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan")
```

### Message Model (`backend/app/models/message.py`)
```python
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    metadata = Column(JSONB)  # tool_calls, tool_results
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
```

### MemoryFact Model (`backend/app/models/memory_fact.py`)
```python
class MemoryFact(Base):
    __tablename__ = "memory_facts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fact_type = Column(String, nullable=False, index=True)  # 'preference', 'goal', 'context'
    content = Column(Text, nullable=False)
    source_conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memory_facts")
```

### PendingAction Model (`backend/app/models/pending_action.py`)
```python
class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    action_type = Column(String, nullable=False)
    params = Column(JSONB, nullable=False)
    status = Column(String, default="pending", index=True)  # 'pending', 'confirmed', 'rejected'
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="pending_actions")
```

### Skill Model (`backend/app/models/skill.py`)
```python
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL for system skills
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    is_system = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="skills")
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
