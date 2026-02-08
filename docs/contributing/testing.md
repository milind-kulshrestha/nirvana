# Testing Guidelines

Testing strategy and guidelines for the Nirvana project.

## Testing Philosophy

- **Test behavior, not implementation** - Focus on what the code does, not how
- **Write tests first** - TDD approach when possible
- **Keep tests simple** - Each test should verify one specific behavior
- **Fast feedback** - Tests should run quickly for rapid development

## Backend Testing (Python/FastAPI)

### Test Structure
```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_auth.py         # Authentication tests
├── test_watchlists.py   # Watchlist functionality tests
├── test_securities.py   # Stock data tests
└── integration/         # Integration tests
    └── test_api.py      # Full API workflow tests
```

### Running Tests
```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app

# Run specific test file
docker-compose exec backend pytest tests/test_auth.py

# Run with verbose output
docker-compose exec backend pytest -v
```

### Test Categories

#### Unit Tests
Test individual functions and methods in isolation.

```python
# tests/test_auth.py
import pytest
from app.lib.auth import hash_password, verify_password

def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password  # Should be hashed
    assert verify_password(password, hashed)  # Should verify correctly
    assert not verify_password("wrong_password", hashed)  # Should reject wrong password
```

#### Integration Tests
Test API endpoints and database interactions.

```python
# tests/test_watchlists.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_watchlist(authenticated_user):
    """Test creating a new watchlist."""
    response = client.post(
        "/watchlists/",
        json={"name": "Tech Stocks"},
        cookies=authenticated_user.cookies
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tech Stocks"
    assert "id" in data
```

### Test Fixtures
```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

@pytest.fixture
def test_db():
    """Create test database session."""
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def authenticated_user(test_db):
    """Create authenticated user for testing."""
    # Create user and return auth cookies
    pass
```

### Mocking External APIs
```python
# tests/test_securities.py
import pytest
from unittest.mock import patch, MagicMock
from app.lib.openbb import get_quote

@patch('app.lib.openbb.obb.equity.price.quote')
def test_get_quote_success(mock_quote):
    """Test successful stock quote retrieval."""
    # Arrange
    mock_quote.return_value = MagicMock(
        results=[{"symbol": "AAPL", "price": 150.00}]
    )
    
    # Act
    result = get_quote("AAPL")
    
    # Assert
    assert result["symbol"] == "AAPL"
    assert result["price"] == 150.00
    mock_quote.assert_called_once_with("AAPL")
```

## Frontend Testing (React)

### Test Structure
```
frontend/src/
├── __tests__/           # Test files
│   ├── components/      # Component tests
│   ├── pages/          # Page tests
│   └── stores/         # State management tests
├── __mocks__/          # Mock files
└── setupTests.js       # Test configuration
```

### Running Tests
```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm test -- --watch

# Run specific test file
npm test -- UserProfile.test.jsx
```

### Component Testing
```javascript
// __tests__/components/StockRow.test.jsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import StockRow from '../../components/StockRow'

const mockStock = {
  symbol: 'AAPL',
  name: 'Apple Inc.',
  price: 150.00,
  change: 2.50
}

test('displays stock information correctly', () => {
  render(<StockRow stock={mockStock} />)
  
  expect(screen.getByText('AAPL')).toBeInTheDocument()
  expect(screen.getByText('Apple Inc.')).toBeInTheDocument()
  expect(screen.getByText('$150.00')).toBeInTheDocument()
  expect(screen.getByText('+$2.50')).toBeInTheDocument()
})

test('handles remove button click', async () => {
  const mockOnRemove = jest.fn()
  const user = userEvent.setup()
  
  render(<StockRow stock={mockStock} onRemove={mockOnRemove} />)
  
  const removeButton = screen.getByRole('button', { name: /remove/i })
  await user.click(removeButton)
  
  expect(mockOnRemove).toHaveBeenCalledWith(mockStock.symbol)
})
```

### Store Testing (Zustand)
```javascript
// __tests__/stores/authStore.test.js
import { renderHook, act } from '@testing-library/react'
import { useAuthStore } from '../../stores/authStore'

test('login updates user state', () => {
  const { result } = renderHook(() => useAuthStore())
  
  act(() => {
    result.current.login({ id: 1, email: 'test@example.com' })
  })
  
  expect(result.current.user).toEqual({
    id: 1,
    email: 'test@example.com'
  })
  expect(result.current.isAuthenticated).toBe(true)
})
```

### Mocking API Calls
```javascript
// __mocks__/api.js
export const mockApi = {
  getWatchlists: jest.fn(() => 
    Promise.resolve([
      { id: 1, name: 'Tech Stocks' },
      { id: 2, name: 'Blue Chips' }
    ])
  ),
  
  createWatchlist: jest.fn((data) =>
    Promise.resolve({ id: 3, ...data })
  )
}

// In test files
import { mockApi } from '../__mocks__/api'

beforeEach(() => {
  jest.clearAllMocks()
})
```

## Database Testing

### Test Database Setup
```python
# Use separate test database
TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/test_watchlist"

# Reset database between tests
@pytest.fixture(autouse=True)
def reset_db():
    """Reset database state between tests."""
    # Truncate all tables
    # Reset sequences
    pass
```

### Migration Testing
```bash
# Test migrations up and down
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
```

## Continuous Integration

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          docker-compose up -d db
          docker-compose run backend pytest --cov=app
          
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Run frontend tests
        run: |
          cd frontend
          npm ci
          npm run test:coverage
```

## Coverage Goals

- **Backend:** Minimum 80% code coverage
- **Frontend:** Minimum 70% code coverage
- **Critical paths:** 100% coverage (auth, data persistence)

## Best Practices

### Do's
- Write descriptive test names that explain the scenario
- Use arrange-act-assert pattern
- Test edge cases and error conditions
- Keep tests independent and isolated
- Use meaningful assertions

### Don'ts
- Don't test implementation details
- Don't write overly complex tests
- Don't ignore failing tests
- Don't skip testing error handling
- Don't test third-party library code

## Debugging Tests

### Common Issues
```bash
# Database connection issues
docker-compose exec backend pytest -v --tb=short

# Frontend test timeouts
npm test -- --verbose --detectOpenHandles

# Mock not working
# Check import paths and mock setup
```

### Test Debugging Tools
- Use `pytest.set_trace()` for backend debugging
- Use `screen.debug()` in React Testing Library
- Check test coverage reports for missed cases
