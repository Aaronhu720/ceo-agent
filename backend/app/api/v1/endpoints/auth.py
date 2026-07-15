from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.organization import Organization
from app.models.user import User, Role
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organization(name=req.organization_name, timezone=req.timezone)
    db.add(org)
    await db.flush()

    owner_role = await db.execute(select(Role).where(Role.name == "owner"))
    role = owner_role.scalar_one_or_none()
    if not role:
        role = Role(name="owner", description="Organization owner")
        db.add(role)
        await db.flush()

    user = User(
        organization_id=org.id,
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        language=req.language,
        timezone=req.timezone,
        role_id=role.id,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id, org.id),
        refresh_token=create_refresh_token(user.id, org.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email, User.status == "active"))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id, user.organization_id),
        refresh_token=create_refresh_token(user.id, user.organization_id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = UUID(payload["sub"])
    org_id = UUID(payload["org"])

    result = await db.execute(select(User).where(User.id == user_id, User.status == "active"))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user_id, org_id),
        refresh_token=create_refresh_token(user_id, org_id),
    )


@router.post("/logout")
async def logout():
    return {"success": True, "message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    role_name = None
    if current_user.role:
        role_name = current_user.role.name
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        organization_id=current_user.organization_id,
        avatar_url=current_user.avatar_url,
        language=current_user.language,
        timezone=current_user.timezone,
        role_name=role_name,
    )
