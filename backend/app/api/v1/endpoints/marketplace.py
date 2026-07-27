"""Generic marketplace management API — supports all platforms."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.marketplace import MarketplaceAccount, MarketplaceListing, PLATFORMS

router = APIRouter()


class AccountCreate(BaseModel):
    platform: str
    site_id: str
    app_key: str | None = None
    app_secret: str | None = None


class AccountUpdate(BaseModel):
    app_key: str | None = None
    app_secret: str | None = None
    shop_name: str | None = None
    seller_id: str | None = None
    status: str | None = None
    extra_config: dict | None = None


# --- Platform config ---

@router.get("/platforms")
async def list_platforms():
    return [
        {"key": k, "name": v["name"], "site_count": len(v["sites"])}
        for k, v in PLATFORMS.items()
    ]


@router.get("/platforms/{platform}/sites")
async def list_platform_sites(platform: str):
    p = PLATFORMS.get(platform)
    if not p:
        raise HTTPException(404, f"Unknown platform: {platform}")
    return [
        {"site_id": k, "name": v["name"], "domain": v["domain"], "currency": v["currency"], "country": v["country"]}
        for k, v in p["sites"].items()
    ]


# --- Accounts ---

@router.get("/accounts")
async def list_accounts(
    platform: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(MarketplaceAccount).where(
        MarketplaceAccount.organization_id == current_user.organization_id,
    )
    if platform:
        query = query.where(MarketplaceAccount.platform == platform)
    query = query.order_by(MarketplaceAccount.created_at.desc())
    result = await db.execute(query)
    return [_serialize_account(a) for a in result.scalars().all()]


@router.post("/accounts")
async def create_account(
    body: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = PLATFORMS.get(body.platform)
    if not p:
        raise HTTPException(400, f"Unknown platform: {body.platform}")
    site = p["sites"].get(body.site_id)
    if not site:
        raise HTTPException(400, f"Unknown site: {body.site_id}")

    existing = await db.execute(
        select(MarketplaceAccount).where(
            MarketplaceAccount.organization_id == current_user.organization_id,
            MarketplaceAccount.site_id == body.site_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(400, f"Account for {body.site_id} already exists")

    account = MarketplaceAccount(
        organization_id=current_user.organization_id,
        platform=body.platform,
        site_id=body.site_id,
        site_name=site["name"],
        country=site["country"],
        app_key=body.app_key,
        app_secret=body.app_secret,
        status="pending",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return _serialize_account(account)


@router.put("/accounts/{account_id}")
async def update_account(
    account_id: UUID,
    body: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_account(db, account_id, current_user.organization_id)
    for field in ("app_key", "app_secret", "shop_name", "seller_id", "status", "extra_config"):
        val = getattr(body, field)
        if val is not None:
            setattr(account, field, val)
    await db.commit()
    await db.refresh(account)
    return _serialize_account(account)


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_account(db, account_id, current_user.organization_id)
    await db.delete(account)
    await db.commit()
    return {"ok": True}


# --- Stats ---

@router.get("/stats")
async def get_stats(
    platform: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = select(func.count(MarketplaceAccount.id)).where(
        MarketplaceAccount.organization_id == current_user.organization_id
    )
    if platform:
        base = base.where(MarketplaceAccount.platform == platform)

    total = (await db.execute(base)).scalar() or 0
    connected = (await db.execute(
        base.where(MarketplaceAccount.status == "connected")
    )).scalar() or 0

    listing_q = select(func.count(MarketplaceListing.id)).where(
        MarketplaceListing.organization_id == current_user.organization_id
    )
    if platform:
        listing_q = listing_q.where(MarketplaceListing.platform == platform)
    listings = (await db.execute(listing_q)).scalar() or 0

    return {"total_accounts": total, "connected_accounts": connected, "total_listings": listings}


# --- Helpers ---

async def _get_account(db: AsyncSession, account_id: UUID, org_id) -> MarketplaceAccount:
    result = await db.execute(
        select(MarketplaceAccount).where(
            MarketplaceAccount.id == account_id,
            MarketplaceAccount.organization_id == org_id,
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(404, "Account not found")
    return account


def _serialize_account(a: MarketplaceAccount) -> dict:
    return {
        "id": str(a.id),
        "platform": a.platform,
        "site_id": a.site_id,
        "site_name": a.site_name,
        "country": a.country,
        "seller_id": a.seller_id,
        "shop_name": a.shop_name,
        "status": a.status,
        "app_key": a.app_key,
        "has_secret": bool(a.app_secret),
        "total_listings": a.total_listings,
        "active_listings": a.active_listings,
        "token_expires_at": a.token_expires_at.isoformat() if a.token_expires_at else None,
        "created_at": a.created_at.isoformat(),
    }
