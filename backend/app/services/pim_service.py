"""PIM (Product Information Management) integration service.

Connects to pim.usaaron.com tRPC API to fetch product data for CEO Agent context.
"""
import structlog
from app.core.config import settings

logger = structlog.get_logger()

_session_cookie: str | None = None


async def _ensure_session() -> str:
    """Login to PIM and cache the session cookie."""
    global _session_cookie
    if _session_cookie:
        return _session_cookie

    import httpx
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        resp = await client.post(
            f"{settings.PIM_BASE_URL}/api/trpc/auth.login",
            json={"json": {"username": settings.PIM_USERNAME, "password": settings.PIM_PASSWORD}},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("result", {}).get("data", {}).get("json", {}).get("success"):
            raise RuntimeError(f"PIM login failed: {data}")

        cookie = resp.headers.get("set-cookie", "")
        session_id = ""
        for part in cookie.split(";"):
            if "app_session_id=" in part:
                session_id = part.strip().split("=", 1)[1] if "=" in part else ""
                break
        if not session_id:
            for c in resp.cookies:
                if c.name == "app_session_id":
                    session_id = c.value
                    break

        if not session_id:
            raise RuntimeError("PIM login succeeded but no session cookie returned")

        _session_cookie = session_id
        logger.info("PIM session established")
        return _session_cookie


def _clear_session():
    global _session_cookie
    _session_cookie = None


async def _trpc_query(procedure: str, input_data: dict | None = None, retry: bool = True) -> dict:
    """Call a tRPC query endpoint on PIM."""
    import httpx
    import json as json_mod
    session = await _ensure_session()

    params = {}
    if input_data is not None:
        params["input"] = json_mod.dumps({"json": input_data})

    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        resp = await client.get(
            f"{settings.PIM_BASE_URL}/api/trpc/{procedure}",
            params=params,
            headers={"Cookie": f"app_session_id={session}"},
        )

        if resp.status_code == 401 and retry:
            _clear_session()
            return await _trpc_query(procedure, input_data, retry=False)

        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"PIM tRPC error: {data['error']}")

        return data.get("result", {}).get("data", {}).get("json", {})


async def get_products(limit: int = 50, search: str | None = None, category: str | None = None) -> dict:
    """Fetch product list from PIM."""
    params = {"limit": limit}
    if search:
        params["search"] = search
    if category:
        params["category"] = category
    return await _trpc_query("products.list", params)


async def get_inventory() -> dict:
    """Fetch inventory with stock levels."""
    return await _trpc_query("inventory.listWithStock", {})


async def get_product_summary() -> str:
    """Get a formatted summary of products for AI context."""
    try:
        data = await get_products(limit=100)
        items = data.get("items", [])
        total = data.get("total", len(items))

        categories = {}
        low_stock = []
        out_of_stock = []

        for p in items:
            cat = p.get("category") or "未分类"
            categories[cat] = categories.get(cat, 0) + 1
            stock = p.get("stockQuantity", 0)
            sku = p.get("sku", "unknown")
            name = p.get("subCategory") or p.get("category") or sku

            if stock == 0:
                out_of_stock.append(f"{sku} ({name})")
            elif stock < 10:
                low_stock.append(f"{sku} ({name}) - 库存:{stock}")

        lines = [f"## PIM产品数据 (共{total}个产品)"]
        lines.append(f"\n### 产品分类分布:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            lines.append(f"- {cat}: {count}个")

        if out_of_stock:
            lines.append(f"\n### ⚠️ 缺货产品 ({len(out_of_stock)}个):")
            for item in out_of_stock[:10]:
                lines.append(f"- {item}")
            if len(out_of_stock) > 10:
                lines.append(f"- ...还有{len(out_of_stock)-10}个")

        if low_stock:
            lines.append(f"\n### ⚠️ 低库存产品 ({len(low_stock)}个):")
            for item in low_stock[:10]:
                lines.append(f"- {item}")

        lines.append(f"\n### 最近产品样本:")
        for p in items[:10]:
            sku = p.get("sku", "?")
            cat = p.get("category", "?")
            sub = p.get("subCategory", "")
            stock = p.get("stockQuantity", 0)
            brand = p.get("brand", "")
            status = p.get("status", "?")
            line = f"- {sku} | {cat}"
            if sub:
                line += f"/{sub}"
            if brand and brand != "Needs Review":
                line += f" | 品牌:{brand}"
            line += f" | 库存:{stock} | {status}"
            lines.append(line)

        return "\n".join(lines)
    except Exception as e:
        logger.warning("Failed to get PIM product summary", error=str(e))
        return ""


async def search_products(query: str) -> str:
    """Search products and return formatted results."""
    try:
        data = await get_products(limit=20, search=query)
        items = data.get("items", [])
        if not items:
            return f"PIM搜索 \"{query}\": 无结果"

        lines = [f"PIM搜索 \"{query}\" 找到 {len(items)} 个产品:"]
        for p in items:
            sku = p.get("sku", "?")
            cat = p.get("category", "?")
            sub = p.get("subCategory", "")
            stock = p.get("stockQuantity", 0)
            brand = p.get("brand", "")
            material = p.get("material", "")
            cost = p.get("costUsd") or ""
            price = p.get("sellingPriceUsd") or ""

            line = f"- {sku} | {cat}"
            if sub:
                line += f"/{sub}"
            if brand and brand != "Needs Review":
                line += f" | 品牌:{brand}"
            if material and material != "Needs Review":
                line += f" | 材质:{material}"
            line += f" | 库存:{stock}"
            if cost:
                line += f" | 成本:${cost}"
            if price:
                line += f" | 售价:${price}"
            lines.append(line)

        return "\n".join(lines)
    except Exception as e:
        logger.warning("PIM search failed", error=str(e))
        return f"PIM搜索失败: {str(e)}"
