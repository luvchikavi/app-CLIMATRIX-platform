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
from sqlmodel import select

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
    result = await session.execute(select(User).where(User.email == form_data.username))
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


# ============================================================================
# Password Reset
# ============================================================================

class ForgotPasswordRequest(BaseModel):
    """Request password reset email."""
    email: str


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str
    new_password: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


def create_password_reset_token(user_id: str) -> str:
    """Create a password reset token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.password_reset_token_expire_minutes)
    to_encode = {"sub": user_id, "exp": expire, "type": "password_reset"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Request a password reset email.

    Always returns success to prevent email enumeration attacks.
    """
    from app.services.email import email_service

    # Find user by email
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Create reset token
        reset_token = create_password_reset_token(str(user.id))

        # Send email
        email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.full_name or user.email,
        )

    # Always return success to prevent email enumeration
    return MessageResponse(message="If an account exists with this email, you will receive a password reset link.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Reset password using the token from the email.
    """
    try:
        payload = jwt.decode(data.token, settings.secret_key, algorithms=[settings.algorithm])

        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token")

        # Find user
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="User account is inactive")

        # Update password
        user.hashed_password = get_password_hash(data.new_password)
        session.add(user)
        await session.commit()

        return MessageResponse(message="Password has been reset successfully. You can now log in with your new password.")

    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")


# ============================================================================
# User Invitations
# ============================================================================

class InviteUserRequest(BaseModel):
    """Request to invite a user."""
    email: str
    role: str = "editor"  # viewer, editor, admin


class InvitationResponse(BaseModel):
    """Invitation response."""
    id: str
    email: str
    role: str
    status: str
    invited_by_email: str
    created_at: str
    expires_at: str


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""
    token: str
    full_name: str
    password: str


@router.post("/invitations", response_model=InvitationResponse)
async def invite_user(
    data: InviteUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Invite a new user to the organization.
    Requires admin role.
    """
    from app.models.core import UserRole, Invitation, InvitationStatus, Organization
    from app.services.email import EmailService
    import secrets

    # Check if user is admin
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can invite users")

    # Check if email already exists
    existing_user = await session.execute(
        select(User).where(User.email == data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Check for existing pending invitation
    existing_invite = await session.execute(
        select(Invitation).where(
            Invitation.email == data.email,
            Invitation.organization_id == current_user.organization_id,
            Invitation.status == InvitationStatus.PENDING
        )
    )
    if existing_invite.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="An invitation is already pending for this email")

    # Parse role
    try:
        role = UserRole(data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {data.role}")

    # Create invitation token
    token = secrets.token_urlsafe(32)

    # Create invitation
    invitation = Invitation(
        organization_id=current_user.organization_id,
        email=data.email,
        role=role,
        invited_by_id=current_user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7),  # 7 day expiration
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)

    # Get organization name for email
    org_result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one()

    # Send invitation email
    email_service = EmailService()
    try:
        await email_service.send_invitation_email(
            to_email=data.email,
            invitation_token=token,
            organization_name=org.name,
            inviter_name=current_user.full_name or current_user.email,
        )
    except Exception as e:
        # Log error but don't fail - invitation is created
        print(f"Failed to send invitation email: {e}")

    return InvitationResponse(
        id=str(invitation.id),
        email=invitation.email,
        role=invitation.role.value,
        status=invitation.status.value,
        invited_by_email=current_user.email,
        created_at=invitation.created_at.isoformat(),
        expires_at=invitation.expires_at.isoformat(),
    )


@router.get("/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    List all invitations for the organization.
    Requires admin role.
    """
    from app.models.core import UserRole, Invitation

    # Check if user is admin
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can view invitations")

    result = await session.execute(
        select(Invitation).where(
            Invitation.organization_id == current_user.organization_id
        ).order_by(Invitation.created_at.desc())
    )
    invitations = result.scalars().all()

    responses = []
    for inv in invitations:
        # Get inviter email
        inviter_result = await session.execute(
            select(User).where(User.id == inv.invited_by_id)
        )
        inviter = inviter_result.scalar_one_or_none()

        responses.append(InvitationResponse(
            id=str(inv.id),
            email=inv.email,
            role=inv.role.value,
            status=inv.status.value,
            invited_by_email=inviter.email if inviter else "Unknown",
            created_at=inv.created_at.isoformat(),
            expires_at=inv.expires_at.isoformat(),
        ))

    return responses


@router.get("/invitations/{invitation_id}/check")
async def check_invitation(
    invitation_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Check if an invitation token is valid (public endpoint for accept page).
    """
    from app.models.core import Invitation, InvitationStatus, Organization

    # Find invitation by token
    result = await session.execute(
        select(Invitation).where(Invitation.token == invitation_id)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Invitation is {invitation.status.value}")

    if invitation.expires_at < datetime.utcnow():
        # Update status to expired
        invitation.status = InvitationStatus.EXPIRED
        session.add(invitation)
        await session.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")

    # Get organization
    org_result = await session.execute(
        select(Organization).where(Organization.id == invitation.organization_id)
    )
    org = org_result.scalar_one()

    return {
        "email": invitation.email,
        "role": invitation.role.value,
        "organization_name": org.name,
        "expires_at": invitation.expires_at.isoformat(),
    }


@router.post("/invitations/accept", response_model=Token)
async def accept_invitation(
    data: AcceptInvitationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Accept an invitation and create user account.
    """
    from app.models.core import Invitation, InvitationStatus, Organization

    # Find invitation
    result = await session.execute(
        select(Invitation).where(Invitation.token == data.token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Invitation is {invitation.status.value}")

    if invitation.expires_at < datetime.utcnow():
        invitation.status = InvitationStatus.EXPIRED
        session.add(invitation)
        await session.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")

    # Check email not already registered
    existing_user = await session.execute(
        select(User).where(User.email == invitation.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    new_user = User(
        email=invitation.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        organization_id=invitation.organization_id,
        role=invitation.role,
        is_active=True,
    )
    session.add(new_user)

    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_at = datetime.utcnow()
    session.add(invitation)

    await session.commit()
    await session.refresh(new_user)

    # Get organization
    org_result = await session.execute(
        select(Organization).where(Organization.id == new_user.organization_id)
    )
    organization = org_result.scalar_one()

    # Create tokens
    token_data = {
        "sub": str(new_user.id),
        "org_id": str(new_user.organization_id),
        "role": new_user.role.value,
    }

    access_token = create_access_token(
        token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value,
            organization_id=str(new_user.organization_id),
        ),
        organization=OrganizationResponse(
            id=str(organization.id),
            name=organization.name,
            country_code=organization.country_code,
        ),
    )


@router.post("/invitations/{invitation_id}/resend")
async def resend_invitation(
    invitation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Resend an invitation email.
    """
    from app.models.core import UserRole, Invitation, InvitationStatus, Organization
    from app.services.email import EmailService
    import secrets

    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can resend invitations")

    result = await session.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.organization_id == current_user.organization_id,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only resend pending invitations")

    # Generate new token and extend expiration
    invitation.token = secrets.token_urlsafe(32)
    invitation.expires_at = datetime.utcnow() + timedelta(days=7)
    session.add(invitation)
    await session.commit()

    # Get organization
    org_result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one()

    # Send email
    email_service = EmailService()
    try:
        await email_service.send_invitation_email(
            to_email=invitation.email,
            invitation_token=invitation.token,
            organization_name=org.name,
            inviter_name=current_user.full_name or current_user.email,
        )
    except Exception as e:
        print(f"Failed to send invitation email: {e}")

    return {"message": "Invitation resent successfully"}


@router.delete("/invitations/{invitation_id}")
async def cancel_invitation(
    invitation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Cancel a pending invitation.
    """
    from app.models.core import UserRole, Invitation, InvitationStatus

    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can cancel invitations")

    result = await session.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.organization_id == current_user.organization_id,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only cancel pending invitations")

    invitation.status = InvitationStatus.CANCELED
    session.add(invitation)
    await session.commit()

    return {"message": "Invitation canceled"}
