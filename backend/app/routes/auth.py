"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.lib.auth import hash_password, verify_password, create_session_token, decode_session_token
from app.lib.validators import validate_email, validate_password
from app.config import settings

router = APIRouter()


# Pydantic schemas
class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    email: str


# Dependency to get current user from session
async def get_current_user(
    session: str = Cookie(default=None), db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from session cookie."""
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = decode_session_token(session)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        request: Registration request with email and password
        db: Database session

    Returns:
        User response with user_id and email

    Raises:
        HTTPException: If email is already registered or validation fails
    """
    # Validate input
    email = validate_email(request.email)
    password = validate_password(request.password)

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = hash_password(password)
    new_user = User(email=email, password_hash=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(user_id=new_user.id, email=new_user.email)


@router.post("/login", response_model=UserResponse)
async def login(
    request: LoginRequest, response: Response, db: Session = Depends(get_db)
):
    """
    Login user and create session.

    Args:
        request: Login request with email and password
        response: FastAPI response to set cookie
        db: Database session

    Returns:
        User response with user_id and email

    Raises:
        HTTPException: If credentials are invalid
    """
    # Validate email
    email = validate_email(request.email)

    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create session token
    session_token = create_session_token(user.id)

    # Set secure HTTP-only cookie
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=not settings.DEBUG,  # HTTPS only in production
        samesite="lax",
        max_age=86400 * 7,  # 7 days
    )

    return UserResponse(user_id=user.id, email=user.email)


@router.post("/logout", status_code=204)
async def logout(response: Response):
    """
    Logout user by clearing session cookie.

    Args:
        response: FastAPI response to clear cookie

    Returns:
        204 No Content
    """
    response.delete_cookie(
        key="session",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from session

    Returns:
        User response with user_id and email
    """
    return UserResponse(user_id=current_user.id, email=current_user.email)
