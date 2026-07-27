"""Mercado Libre listing creation service.

Pulls product data from PIM, maps to ML categories, generates
Spanish-language titles/descriptions, and publishes via ML API.
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

ML_API = "https://api.mercadolibre.com"


async def search_ml_category(query: str, site_id: str = "MLM") -> list[dict]:
    """Search ML category tree by keyword using domain discovery."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{ML_API}/sites/{site_id}/domain_discovery/search",
            params={"q": query},
        )
        if resp.status_code == 200:
            results = resp.json()
            if results:
                return results[:5]
        return []


async def predict_category(title: str, site_id: str = "MLM") -> Optional[str]:
    """Predict the best ML category for a product title using domain discovery."""
    # Try domain discovery first (more reliable)
    results = await search_ml_category(title, site_id)
    if results:
        return results[0].get("category_id")

    # Try with individual words if full title fails
    words = title.split()
    for i in range(len(words), 0, -1):
        partial = " ".join(words[:i])
        results = await search_ml_category(partial, site_id)
        if results:
            return results[0].get("category_id")

    return None


async def get_category_attributes(category_id: str) -> list[dict]:
    """Get required and optional attributes for a ML category."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{ML_API}/categories/{category_id}/attributes")
        if resp.status_code == 200:
            return resp.json()
        return []


async def generate_ml_listing_data(
    product: dict,
    access_token: str,
    site_id: str = "MLM",
    price_override: float | None = None,
    currency: str = "MXN",
) -> dict:
    """Build a ML listing payload from PIM product data.

    Returns a dict ready to POST to /items.
    """
    sku = product.get("sku", "")
    category = product.get("category", "")
    sub_category = product.get("subCategory", "")
    brand = product.get("brand", "")
    material = product.get("material", "")
    color = product.get("color", "")
    stock = product.get("stockQuantity", 0)

    if brand and brand.lower() in ("needs review", "n/a", ""):
        brand = "Dr Camp"

    # Build search query for category prediction
    search_parts = [p for p in [category, sub_category, brand] if p]
    search_query = " ".join(search_parts) if search_parts else sku

    # Generate title (ML max 60 chars)
    title_parts = []
    if brand and brand != "Dr Camp":
        title_parts.append(brand)
    if sub_category:
        title_parts.append(sub_category)
    elif category:
        title_parts.append(category)
    if material and material.lower() not in ("needs review", "n/a"):
        title_parts.append(material)
    if color and color.lower() not in ("needs review", "n/a"):
        title_parts.append(color)

    title = " ".join(title_parts)
    if not title:
        title = sku

    # Predict ML category
    ml_category_id = await predict_category(search_query, site_id)
    if not ml_category_id:
        ml_category_id = await predict_category(title, site_id)

    # Build attributes
    attributes = []
    if brand:
        attributes.append({"id": "BRAND", "value_name": brand})
    if product.get("countryOfOrigin"):
        attributes.append({"id": "ORIGIN", "value_name": product["countryOfOrigin"]})
    if material and material.lower() not in ("needs review", "n/a"):
        attributes.append({"id": "MATERIAL", "value_name": material})
    if color and color.lower() not in ("needs review", "n/a"):
        attributes.append({"id": "COLOR", "value_name": color})
    # CBT items are always new
    attributes.append({"id": "ITEM_CONDITION", "value_name": "Nuevo"})

    # Price
    price = price_override
    if price is None:
        selling_price = product.get("sellingPriceUsd")
        if selling_price:
            price = float(selling_price)
            if currency == "MXN":
                price = round(price * 18.5, 2)  # Rough USD->MXN
        else:
            cost = product.get("costUsd")
            if cost:
                price = round(float(cost) * 3.5, 2)  # 3.5x markup
                if currency == "MXN":
                    price = round(price * 18.5, 2)

    listing_data = {
        "title": title[:60],
        "category_id": ml_category_id,
        "price": price or 999,
        "currency_id": currency,
        "available_quantity": min(stock, 100) if stock > 0 else 1,
        "buying_mode": "buy_it_now",
        "listing_type_id": "gold_special",
        "condition": "new",
        "attributes": attributes,
        "seller_custom_field": sku,
    }

    # Add description
    desc_parts = []
    if sub_category:
        desc_parts.append(sub_category)
    if brand:
        desc_parts.append(f"Marca: {brand}")
    if material and material.lower() not in ("needs review", "n/a"):
        desc_parts.append(f"Material: {material}")
    if color and color.lower() not in ("needs review", "n/a"):
        desc_parts.append(f"Color: {color}")

    dimensions = []
    if product.get("productLengthCm"):
        dimensions.append(f"Largo: {product['productLengthCm']}cm")
    if product.get("productWidthCm"):
        dimensions.append(f"Ancho: {product['productWidthCm']}cm")
    if product.get("productHeightCm"):
        dimensions.append(f"Alto: {product['productHeightCm']}cm")
    if product.get("productWeightKg"):
        dimensions.append(f"Peso: {product['productWeightKg']}kg")
    if dimensions:
        desc_parts.append("Dimensiones: " + ", ".join(dimensions))

    desc_parts.append("Envío internacional desde Estados Unidos")
    desc_parts.append(f"SKU: {sku}")

    listing_data["_description"] = "\n".join(desc_parts)

    return listing_data


async def publish_to_ml(
    listing_data: dict,
    access_token: str,
) -> dict:
    """Publish a listing to Mercado Libre Items API."""
    description_text = listing_data.pop("_description", "")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create the item
        resp = await client.post(
            f"{ML_API}/items",
            json=listing_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if resp.status_code not in (200, 201):
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"error": resp.text}
            logger.error("ML publish failed: %s", error_data)
            return {"success": False, "error": error_data, "status_code": resp.status_code}

        item = resp.json()
        item_id = item.get("id")

        # Add description
        if description_text and item_id:
            await client.post(
                f"{ML_API}/items/{item_id}/description",
                json={"plain_text": description_text},
                headers={"Authorization": f"Bearer {access_token}"},
            )

        return {
            "success": True,
            "item_id": item_id,
            "permalink": item.get("permalink", ""),
            "title": item.get("title", ""),
            "price": item.get("price"),
            "status": item.get("status", ""),
        }


async def upload_image_to_ml(image_url: str, access_token: str) -> Optional[str]:
    """Upload an image to ML from URL, returns ML image ID."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{ML_API}/pictures",
            json={"source": image_url},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code in (200, 201):
            return resp.json().get("id")
    return None


async def add_images_to_item(item_id: str, image_urls: list[str], access_token: str) -> dict:
    """Add images to an existing ML listing."""
    pictures = []
    for url in image_urls:
        pic_id = await upload_image_to_ml(url, access_token)
        if pic_id:
            pictures.append({"id": pic_id})

    if not pictures:
        return {"success": False, "error": "No images uploaded successfully"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.put(
            f"{ML_API}/items/{item_id}",
            json={"pictures": pictures},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code == 200:
            return {"success": True, "images_added": len(pictures)}
        return {"success": False, "error": resp.text}
