"""Mercado Libre multi-country management API."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.mercadolibre import MLAccount, MLListing, ML_SITES

router = APIRouter()


class AccountCreate(BaseModel):
    site_id: str
    app_id: str | None = None
    app_secret: str | None = None
    redirect_uri: str | None = None


class AccountUpdate(BaseModel):
    app_id: str | None = None
    app_secret: str | None = None
    redirect_uri: str | None = None
    status: str | None = None


class ListingCreate(BaseModel):
    account_id: str
    pim_sku: str | None = None
    title: str
    price: float | None = None
    currency_id: str | None = None
    available_quantity: int = 0
    listing_type: str = "gold_special"
    condition: str = "new"
    category_id: str | None = None


# --- Sites ---

@router.get("/sites")
async def list_sites():
    """List all available Mercado Libre country sites."""
    return [
        {"site_id": k, "country": v["name"], "domain": v["domain"], "currency": v["currency"]}
        for k, v in ML_SITES.items()
    ]


# --- Accounts ---

@router.get("/accounts")
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MLAccount).where(
            MLAccount.organization_id == current_user.organization_id,
        ).order_by(MLAccount.created_at.desc())
    )
    accounts = result.scalars().all()
    return [_serialize_account(a) for a in accounts]


@router.post("/accounts")
async def create_account(
    body: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.site_id not in ML_SITES:
        raise HTTPException(400, f"Invalid site_id: {body.site_id}")

    existing = await db.execute(
        select(MLAccount).where(
            MLAccount.organization_id == current_user.organization_id,
            MLAccount.site_id == body.site_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(400, f"Account for {body.site_id} already exists")

    site = ML_SITES[body.site_id]
    account = MLAccount(
        organization_id=current_user.organization_id,
        site_id=body.site_id,
        country_name=site["name"],
        app_id=body.app_id,
        app_secret=body.app_secret,
        redirect_uri=body.redirect_uri or f"https://ceo.usaaron.com/api/mercadolibre/callback",
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
    if body.app_id is not None:
        account.app_id = body.app_id
    if body.app_secret is not None:
        account.app_secret = body.app_secret
    if body.redirect_uri is not None:
        account.redirect_uri = body.redirect_uri
    if body.status is not None:
        account.status = body.status
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


@router.get("/accounts/{account_id}/auth-url")
async def get_auth_url(
    account_id: UUID,
    cbt: bool = Query(False, description="CBT cross-border seller account"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate OAuth authorization URL for this account."""
    account = await _get_account(db, account_id, current_user.organization_id)
    if not account.app_id:
        raise HTTPException(400, "App ID not configured")

    if cbt:
        auth_base = "https://auth.mercadolibre.com"
    else:
        auth_base = f"https://auth.mercadolibre.com.{_get_auth_domain(account.site_id)}"

    auth_url = (
        f"{auth_base}/authorization?response_type=code"
        f"&client_id={account.app_id}"
        f"&redirect_uri={account.redirect_uri}"
        f"&state={account.id}"
    )
    return {"auth_url": auth_url, "site_id": account.site_id}


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from Mercado Libre."""
    import httpx

    if not state:
        raise HTTPException(400, "Missing state")

    result = await db.execute(select(MLAccount).where(MLAccount.id == state))
    account = result.scalars().first()
    if not account:
        raise HTTPException(404, "Account not found")

    if not account.app_id or not account.app_secret:
        raise HTTPException(400, "App credentials not configured")

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://api.mercadolibre.com/oauth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": account.app_id,
                "client_secret": account.app_secret,
                "code": code,
                "redirect_uri": account.redirect_uri,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(400, f"OAuth token exchange failed: {resp.text}")

        token_data = resp.json()

    from datetime import datetime, timezone, timedelta
    account.access_token = token_data.get("access_token")
    account.refresh_token = token_data.get("refresh_token")
    account.seller_id = str(token_data.get("user_id", ""))
    expires_in = token_data.get("expires_in", 21600)
    account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    account.status = "connected"

    if account.seller_id:
        async with httpx.AsyncClient(timeout=10.0) as client:
            user_resp = await client.get(
                f"https://api.mercadolibre.com/users/{account.seller_id}",
                headers={"Authorization": f"Bearer {account.access_token}"},
            )
            if user_resp.status_code == 200:
                user_data = user_resp.json()
                account.nickname = user_data.get("nickname", "")

    await db.commit()
    return RedirectResponse(url="/mercadolibre?connected=true")


# --- Listings ---

@router.get("/listings")
async def list_listings(
    account_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(MLListing).where(MLListing.organization_id == current_user.organization_id)
    if account_id:
        query = query.where(MLListing.account_id == account_id)
    query = query.order_by(MLListing.created_at.desc()).limit(100)

    result = await db.execute(query)
    listings = result.scalars().all()
    return [_serialize_listing(l) for l in listings]


@router.post("/listings")
async def create_listing(
    body: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_account(db, UUID(body.account_id), current_user.organization_id)
    site = ML_SITES.get(account.site_id, {})

    listing = MLListing(
        organization_id=current_user.organization_id,
        account_id=account.id,
        pim_sku=body.pim_sku,
        title=body.title,
        price=body.price,
        currency_id=body.currency_id or site.get("currency", "USD"),
        available_quantity=body.available_quantity,
        listing_type=body.listing_type,
        condition=body.condition,
        category_id=body.category_id,
        ml_status="draft",
        sync_status="pending",
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return _serialize_listing(listing)


# --- Stats ---

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts_q = await db.execute(
        select(func.count(MLAccount.id)).where(
            MLAccount.organization_id == current_user.organization_id
        )
    )
    connected_q = await db.execute(
        select(func.count(MLAccount.id)).where(
            MLAccount.organization_id == current_user.organization_id,
            MLAccount.status == "connected",
        )
    )
    listings_q = await db.execute(
        select(func.count(MLListing.id)).where(
            MLListing.organization_id == current_user.organization_id
        )
    )
    return {
        "total_accounts": accounts_q.scalar() or 0,
        "connected_accounts": connected_q.scalar() or 0,
        "total_listings": listings_q.scalar() or 0,
    }


# --- Helpers ---

async def _get_account(db: AsyncSession, account_id: UUID, org_id) -> MLAccount:
    result = await db.execute(
        select(MLAccount).where(MLAccount.id == account_id, MLAccount.organization_id == org_id)
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(404, "Account not found")
    return account


def _get_auth_domain(site_id: str) -> str:
    domain_map = {
        "MLM": "mx", "MLB": "br", "MLC": "cl", "MLA": "ar",
        "MCO": "co", "MLU": "uy", "MPE": "pe", "MEC": "ec",
    }
    return domain_map.get(site_id, "ar")


def _serialize_account(a: MLAccount) -> dict:
    return {
        "id": str(a.id),
        "site_id": a.site_id,
        "country_name": a.country_name,
        "seller_id": a.seller_id,
        "nickname": a.nickname,
        "status": a.status,
        "app_id": a.app_id,
        "has_secret": bool(a.app_secret),
        "redirect_uri": a.redirect_uri,
        "total_listings": a.total_listings,
        "active_listings": a.active_listings,
        "token_expires_at": a.token_expires_at.isoformat() if a.token_expires_at else None,
        "created_at": a.created_at.isoformat(),
    }


def _serialize_listing(l: MLListing) -> dict:
    return {
        "id": str(l.id),
        "account_id": str(l.account_id),
        "ml_item_id": l.ml_item_id,
        "pim_sku": l.pim_sku,
        "title": l.title,
        "price": l.price,
        "currency_id": l.currency_id,
        "available_quantity": l.available_quantity,
        "listing_type": l.listing_type,
        "condition": l.condition,
        "permalink": l.permalink,
        "thumbnail": l.thumbnail,
        "ml_status": l.ml_status,
        "sync_status": l.sync_status,
        "sync_error": l.sync_error,
        "last_synced_at": l.last_synced_at.isoformat() if l.last_synced_at else None,
        "created_at": l.created_at.isoformat(),
    }
