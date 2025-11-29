"""Input validation utilities."""
import re
from fastapi import HTTPException


def validate_email(email: str) -> str:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Cleaned email address

    Raises:
        HTTPException: If email is invalid
    """
    email = email.strip().lower()
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    return email


def validate_password(password: str) -> str:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Password if valid

    Raises:
        HTTPException: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long"
        )

    return password


def validate_watchlist_name(name: str) -> str:
    """
    Validate watchlist name.

    Args:
        name: Watchlist name to validate

    Returns:
        Cleaned watchlist name

    Raises:
        HTTPException: If name is invalid
    """
    name = name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Watchlist name cannot be empty")

    if len(name) > 50:
        raise HTTPException(
            status_code=400, detail="Watchlist name cannot exceed 50 characters"
        )

    return name


def validate_symbol(symbol: str) -> str:
    """
    Validate stock ticker symbol format.

    Args:
        symbol: Ticker symbol to validate

    Returns:
        Uppercase symbol

    Raises:
        HTTPException: If symbol format is invalid
    """
    symbol = symbol.strip().upper()

    # Basic validation: alphanumeric, dash, and dot (for crypto like BTC-USD)
    symbol_pattern = r"^[A-Z0-9.-]+$"

    if not re.match(symbol_pattern, symbol):
        raise HTTPException(
            status_code=400,
            detail="Invalid symbol format. Use letters, numbers, dots, and dashes only",
        )

    if len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Symbol cannot exceed 20 characters")

    return symbol
