# Code Style Guide

Coding conventions and style guidelines for the Nirvana project.

## General Principles

- **Consistency** - Follow established patterns in the codebase
- **Clarity** - Write self-documenting code with meaningful names
- **Simplicity** - Prefer simple, readable solutions over clever ones
- **Testing** - Write tests for new functionality

## Backend (Python/FastAPI)

### Code Style
- Follow **PEP 8** style guidelines
- Use **Black** for code formatting
- Use **type hints** for all function parameters and return values
- Maximum line length: **88 characters** (Black default)

### Naming Conventions
```python
# Variables and functions: snake_case
user_email = "user@example.com"
def get_user_by_id(user_id: int) -> User:

# Classes: PascalCase  
class UserService:
class WatchlistItem:

# Constants: UPPER_SNAKE_CASE
MAX_WATCHLIST_ITEMS = 50
DEFAULT_TIMEOUT = 30
```

### File Organization
```
app/
├── models/          # SQLAlchemy models
├── routes/          # FastAPI route handlers
├── lib/            # Business logic and utilities
├── dependencies.py  # FastAPI dependencies
└── main.py         # Application entry point
```

### Error Handling
```python
# Use HTTPException for API errors
from fastapi import HTTPException

if not user:
    raise HTTPException(status_code=404, detail="User not found")

# Use proper logging
import logging
logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

## Frontend (React/JavaScript)

### Code Style
- Use **Prettier** for code formatting
- Use **ESLint** for linting
- Prefer **functional components** with hooks
- Use **TypeScript** for type safety (when applicable)

### Naming Conventions
```javascript
// Components: PascalCase
const UserProfile = () => {}
const WatchlistItem = () => {}

// Variables and functions: camelCase
const userName = "john_doe"
const getUserData = async () => {}

// Constants: UPPER_SNAKE_CASE
const MAX_RETRY_ATTEMPTS = 3
const API_BASE_URL = "http://localhost:8000"

// Files: kebab-case
user-profile.jsx
watchlist-item.jsx
```

### Component Structure
```javascript
// Imports first
import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'

// Component definition
const ComponentName = ({ prop1, prop2 }) => {
  // Hooks at the top
  const [state, setState] = useState(null)
  
  // Event handlers
  const handleClick = () => {
    // Implementation
  }
  
  // Effects
  useEffect(() => {
    // Side effects
  }, [])
  
  // Render
  return (
    <div>
      {/* JSX content */}
    </div>
  )
}

export default ComponentName
```

### State Management
- Use **Zustand** for global state
- Use **useState** for local component state
- Keep state as close to where it's used as possible

## Database (PostgreSQL)

### Schema Design
- Use **snake_case** for table and column names
- Include `created_at` and `updated_at` timestamps
- Use foreign key constraints with CASCADE deletes
- Add appropriate indexes for query performance

### Migration Guidelines
```python
# Always use descriptive migration messages
alembic revision --autogenerate -m "add_user_preferences_table"

# Include both upgrade and downgrade operations
def upgrade():
    # Forward migration
    pass

def downgrade():
    # Reverse migration  
    pass
```

## Testing

### Backend Tests
```python
# Use pytest for testing
# Test files: test_*.py
# Test functions: test_*

def test_create_user():
    # Arrange
    user_data = {"email": "test@example.com"}
    
    # Act
    result = create_user(user_data)
    
    # Assert
    assert result.email == "test@example.com"
```

### Frontend Tests
```javascript
// Use React Testing Library
// Test files: *.test.jsx

import { render, screen } from '@testing-library/react'
import UserProfile from './UserProfile'

test('renders user profile', () => {
  render(<UserProfile user={mockUser} />)
  expect(screen.getByText('User Profile')).toBeInTheDocument()
})
```

## Documentation

### Code Comments
```python
# Use docstrings for functions and classes
def get_stock_quote(symbol: str) -> dict:
    """
    Fetch current stock quote from OpenBB.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        Dictionary containing quote data
        
    Raises:
        HTTPException: If symbol not found or API error
    """
```

### README Updates
- Update relevant README files when adding features
- Include setup instructions for new dependencies
- Document environment variables and configuration

## Git Workflow

### Commit Messages
```bash
# Format: type(scope): description
feat(auth): add session-based authentication
fix(api): handle missing stock symbol error
docs(readme): update installation instructions
refactor(db): optimize watchlist queries
```

### Branch Naming
```bash
# Feature branches
feature/user-authentication
feature/stock-charts

# Bug fixes  
fix/login-redirect-issue
fix/price-update-bug

# Documentation
docs/api-reference
docs/setup-guide
```
