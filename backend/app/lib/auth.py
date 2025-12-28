"""Authentication utilities for password hashing and session management."""
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.config import settings

# Session serializer for signed cookies
session_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Convert to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_session_token(user_id: int) -> str:
    """
    Create a signed session token.

    Args:
        user_id: User ID to encode in session

    Returns:
        Signed session token string
    """
    return session_serializer.dumps({"user_id": user_id})


def decode_session_token(token: str, max_age: int = 86400 * 7) -> dict | None:
    """
    Decode and verify a session token.

    Args:
        token: Signed session token
        max_age: Maximum age of token in seconds (default: 7 days)

    Returns:
        Dictionary with user_id if valid, None otherwise
    """
    try:
        data = session_serializer.loads(token, max_age=max_age)
        return data
    except (BadSignature, SignatureExpired):
        return None
