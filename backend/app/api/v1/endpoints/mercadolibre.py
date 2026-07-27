"""Mercado Libre multi-country management API."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.mercadolibre import MLAccount, MLListing, ML_SITES

logger = logging.getLogger(__name__)
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
    import secrets
    import hashlib
    import base64

    account = await _get_account(db, account_id, current_user.organization_id)
    if not account.app_id:
        raise HTTPException(400, "App ID not configured")

    if cbt:
        auth_base = "https://global-selling.mercadolibre.com"
    else:
        auth_base = f"https://auth.mercadolibre.com.{_get_auth_domain(account.site_id)}"

    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    account.metadata_json = {**(account.metadata_json or {}), "pkce_code_verifier": code_verifier}
    await db.commit()

    auth_url = (
        f"{auth_base}/authorization?response_type=code"
        f"&client_id={account.app_id}"
        f"&redirect_uri={account.redirect_uri}"
        f"&state={account.id}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
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

    token_body = {
        "grant_type": "authorization_code",
        "client_id": account.app_id,
        "client_secret": account.app_secret,
        "code": code,
        "redirect_uri": account.redirect_uri,
    }
    code_verifier = (account.metadata_json or {}).get("pkce_code_verifier")
    if code_verifier:
        token_body["code_verifier"] = code_verifier

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://api.mercadolibre.com/oauth/token",
            json=token_body,
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


# --- Publish from PIM ---

class PublishRequest(BaseModel):
    account_id: str
    pim_sku: str
    price: float | None = None
    currency: str = "MXN"
    title_override: str | None = None
    image_urls: list[str] | None = None


@router.post("/publish-from-pim")
async def publish_from_pim(
    body: PublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch product from PIM, generate ML listing, and publish."""
    from app.services.pim_service import get_products
    from app.services.ml_listing_service import generate_ml_listing_data, publish_to_ml, add_images_to_item

    account = await _get_account(db, UUID(body.account_id), current_user.organization_id)
    if account.status != "connected" or not account.access_token:
        raise HTTPException(400, "Account not connected or token missing")

    # Refresh token if expired
    await _refresh_if_needed(db, account)

    # Find product in PIM
    pim_data = await get_products(limit=50, search=body.pim_sku)
    items = pim_data.get("items", [])
    product = next((p for p in items if p.get("sku") == body.pim_sku), None)
    if not product:
        raise HTTPException(404, f"Product {body.pim_sku} not found in PIM")

    # Generate ML listing data
    listing_data = await generate_ml_listing_data(
        product=product,
        access_token=account.access_token,
        site_id=account.site_id,
        price_override=body.price,
        currency=body.currency,
    )

    if body.title_override:
        listing_data["title"] = body.title_override[:60]

    # Add images if provided
    if body.image_urls:
        from app.services.ml_listing_service import upload_image_to_ml
        pictures = []
        for url in body.image_urls:
            pic_id = await upload_image_to_ml(url, account.access_token)
            if pic_id:
                pictures.append({"id": pic_id})
        if pictures:
            listing_data["pictures"] = pictures

    # Publish to ML
    result = await publish_to_ml(listing_data, account.access_token)

    if result.get("success"):
        # Save to local DB
        listing = MLListing(
            organization_id=current_user.organization_id,
            account_id=account.id,
            ml_item_id=result["item_id"],
            pim_sku=body.pim_sku,
            title=result.get("title", listing_data.get("title", "")),
            price=result.get("price"),
            currency_id=body.currency,
            available_quantity=listing_data.get("available_quantity", 1),
            listing_type=listing_data.get("listing_type_id", "gold_special"),
            condition="new",
            permalink=result.get("permalink", ""),
            ml_status=result.get("status", "active"),
            sync_status="synced",
            category_id=listing_data.get("category_id"),
        )
        db.add(listing)
        await db.commit()
        await db.refresh(listing)

    return result


@router.post("/preview-listing")
async def preview_listing(
    body: PublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview what the ML listing would look like without publishing."""
    from app.services.pim_service import get_products
    from app.services.ml_listing_service import generate_ml_listing_data, get_category_attributes

    account = await _get_account(db, UUID(body.account_id), current_user.organization_id)

    pim_data = await get_products(limit=50, search=body.pim_sku)
    items = pim_data.get("items", [])
    product = next((p for p in items if p.get("sku") == body.pim_sku), None)
    if not product:
        raise HTTPException(404, f"Product {body.pim_sku} not found in PIM")

    listing_data = await generate_ml_listing_data(
        product=product,
        access_token=account.access_token or "",
        site_id=account.site_id,
        price_override=body.price,
        currency=body.currency,
    )

    if body.title_override:
        listing_data["title"] = body.title_override[:60]

    # Get category info
    cat_attrs = []
    if listing_data.get("category_id"):
        cat_attrs = await get_category_attributes(listing_data["category_id"])

    return {
        "listing_data": listing_data,
        "pim_product": product,
        "category_attributes": [
            {"id": a.get("id"), "name": a.get("name"), "required": a.get("tags", {}).get("required", False)}
            for a in cat_attrs[:20]
        ],
    }


@router.post("/listings/{item_id}/add-images")
async def add_listing_images(
    item_id: str,
    image_urls: list[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add images to an existing ML listing."""
    from app.services.ml_listing_service import add_images_to_item

    result = await db.execute(
        select(MLListing).where(
            MLListing.ml_item_id == item_id,
            MLListing.organization_id == current_user.organization_id,
        )
    )
    listing = result.scalars().first()
    if not listing:
        raise HTTPException(404, "Listing not found")

    account = await _get_account(db, listing.account_id, current_user.organization_id)
    await _refresh_if_needed(db, account)

    return await add_images_to_item(item_id, image_urls, account.access_token)


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


# --- Notifications (required by ML security configuration) ---

@router.post("/notifications")
async def ml_notifications(request: Request):
    """Webhook for Mercado Libre IPN (Instant Payment Notifications).
    ML sends notifications about orders, questions, messages, etc."""
    try:
        body = await request.json()
        logger.info("ML notification received: %s", body)
    except Exception:
        pass
    return JSONResponse({"status": "ok"}, status_code=200)


@router.post("/delete-notification")
async def ml_delete_notification(request: Request):
    """Webhook for ML GDPR data deletion requests.
    Required by security configuration."""
    try:
        body = await request.json()
        logger.info("ML delete notification: %s", body)
    except Exception:
        pass
    return JSONResponse({"status": "received"}, status_code=200)


@router.get("/delete-notification")
async def ml_delete_notification_get():
    """GET handler for ML delete notification URL verification."""
    return JSONResponse({"status": "ok"}, status_code=200)


@router.post("/status-notification")
async def ml_status_notification(request: Request):
    """Webhook for ML app status change notifications."""
    try:
        body = await request.json()
        logger.info("ML status notification: %s", body)
    except Exception:
        pass
    return JSONResponse({"status": "received"}, status_code=200)


# --- Helpers ---

async def _refresh_if_needed(db: AsyncSession, account: MLAccount):
    """Refresh access token if expired or about to expire."""
    from datetime import datetime, timezone, timedelta
    import httpx

    if not account.refresh_token or not account.token_expires_at:
        return

    if account.token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=30):
        return

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.mercadolibre.com/oauth/token",
                json={
                    "grant_type": "refresh_token",
                    "client_id": account.app_id,
                    "client_secret": account.app_secret,
                    "refresh_token": account.refresh_token,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                account.access_token = data.get("access_token")
                account.refresh_token = data.get("refresh_token", account.refresh_token)
                expires_in = data.get("expires_in", 21600)
                account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                await db.commit()
                logger.info("ML token refreshed for account %s", account.id)
    except Exception as e:
        logger.error("Token refresh failed: %s", e)


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
