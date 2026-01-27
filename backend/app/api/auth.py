"""
Authentication API endpoints.
Handles login, logout, and token refresh.
"""
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.config import settings
from app.database import get_session
from app.models.core import User

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v3/auth/login")


# ============================================================================
# Schemas
# ============================================================================

class UserResponse(BaseModel):
    """User response (public)."""
    id: str
    email: str
    full_name: str | None
    role: str
    organization_id: str


class OrganizationResponse(BaseModel):
    """Organization response (public)."""
    id: str
    name: str
    country_code: str | None


class Token(BaseModel):
    """Token response - includes user and org for frontend state."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: OrganizationResponse | None


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    org_id: str
    role: str


# ============================================================================
# Helpers
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Authenticate user and return JWT tokens with user/org data."""
    from app.models.core import Organization

    # Find user by email
    # Case-insensitive email lookup for login
    result = await session.execute(select(User).where(func.lower(User.email) == form_data.username.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Fetch organization
    org_result = await session.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    organization = org_result.scalar_one_or_none()

    # Update last login
    user.last_login = datetime.utcnow()
    session.add(user)
    await session.commit()

    # Create tokens with org_id for multi-tenancy
    token_data = {
        "sub": str(user.id),
        "org_id": str(user.organization_id),
        "role": user.role.value,
    }

    access_token = create_access_token(
        token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_refresh_token(token_data)

    # Build user response
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        organization_id=str(user.organization_id),
    )

    # Build organization response
    org_response = None
    if organization:
        org_response = OrganizationResponse(
            id=str(organization.id),
            name=organization.name,
            country_code=organization.country_code,
        )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response,
        organization=org_response,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user_id = payload.get("sub")
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=400, detail="Invalid user")

        token_data = {
            "sub": str(user.id),
            "org_id": str(user.organization_id),
            "role": user.role.value,
        }

        new_access_token = create_access_token(
            token_data,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        new_refresh_token = create_refresh_token(token_data)

        return Token(access_token=new_access_token, refresh_token=new_refresh_token)

    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid refresh token")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        organization_id=str(current_user.organization_id),
    )


# ============================================================================
# Registration
# ============================================================================

class RegisterRequest(BaseModel):
    """Registration request - creates organization and admin user."""
    email: str
    password: str
    full_name: str
    organization_name: str
    country_code: str | None = None


@router.post("/register", response_model=Token)
async def register(
    data: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Register a new user and organization.

    Creates:
    1. New organization with the provided name
    2. New user as admin of that organization
    3. Returns tokens so the user is automatically logged in
    """
    from app.models.core import Organization, UserRole

    # Check if email already exists
    result = await session.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create organization
    organization = Organization(
        name=data.organization_name,
        country_code=data.country_code,
        default_region=data.country_code or "Global",
    )
    session.add(organization)
    await session.flush()  # Get the organization ID

    # Create user as admin
    hashed_password = get_password_hash(data.password)
    user = User(
        email=data.email,
        hashed_password=hashed_password,
        full_name=data.full_name,
        organization_id=organization.id,
        role=UserRole.ADMIN,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    await session.refresh(organization)

    # Create tokens
    token_data = {
        "sub": str(user.id),
        "org_id": str(user.organization_id),
        "role": user.role.value,
    }

    access_token = create_access_token(
        token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_refresh_token(token_data)

    # Build responses
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        organization_id=str(user.organization_id),
    )

    org_response = OrganizationResponse(
        id=str(organization.id),
        name=organization.name,
        country_code=organization.country_code,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response,
        organization=org_response,
    )
