# Authentication Guide

Nirvana uses session-based authentication with HTTP-only cookies for security.

## Authentication Flow

### Backend Implementation
- **Session Management:** `app/lib/auth.py` handles bcrypt hashing and session tokens
- **Security:** Uses `itsdangerous` for signed cookies
- **Protection:** Protected routes check session via `get_current_user` dependency

### Frontend Implementation  
- **State Management:** `stores/authStore.js` manages auth state via Zustand
- **Route Protection:** `ProtectedRoute` wrapper component guards authenticated pages
- **Cookie Handling:** HTTP-only cookies automatically managed by browser

## Key Files

**Backend:**
- `backend/app/lib/auth.py` - Session management and password hashing
- `backend/app/routes/auth.py` - Login/logout endpoints
- `backend/app/dependencies.py` - `get_current_user` dependency

**Frontend:**
- `frontend/src/stores/authStore.js` - Authentication state
- `frontend/src/components/ProtectedRoute.jsx` - Route protection
- `frontend/src/pages/Login.jsx` - Login form

## Database Schema

```sql
-- User table stores hashed passwords
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Security Features

- **Password Hashing:** bcrypt with salt rounds
- **Session Tokens:** Cryptographically signed with secret key
- **HTTP-Only Cookies:** Prevents XSS attacks
- **CORS Configuration:** Restricts cross-origin requests
- **Session Expiration:** Configurable timeout

## Usage Examples

### Login Flow
1. User submits email/password to `/auth/login`
2. Backend validates credentials and creates session token
3. Token stored in HTTP-only cookie
4. Frontend auth store updated on successful response
5. User redirected to dashboard

### Protected Route Access
1. Frontend checks auth store state
2. If authenticated, render protected component
3. If not authenticated, redirect to login
4. Backend validates session token on API requests

### Logout Flow
1. User clicks logout
2. Frontend calls `/auth/logout` endpoint
3. Backend clears session cookie
4. Frontend auth store reset
5. User redirected to login page
