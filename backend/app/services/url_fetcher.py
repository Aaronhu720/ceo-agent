"""Shared URL fetching and content extraction for CEO Agent."""
import re
import structlog

logger = structlog.get_logger()


def extract_urls(text: str) -> list[str]:
    return re.findall(r'https?://[^\s<>"\')\]]+', text)


async def fetch_url_content(url: str, max_chars: int = 15000) -> str | None:
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; CEOAgent/1.0)",
                "Accept": "text/html,application/json,text/plain",
            })
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")

            if "application/json" in content_type:
                return resp.text[:max_chars]

            html = resp.text
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
            html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL)
            html = re.sub(r'<[^>]+>', ' ', html)
            html = re.sub(r'\s+', ' ', html).strip()
            text_content = html[:max_chars]
            logger.info("URL content fetched", url=url, length=len(text_content))
            return text_content
    except Exception as e:
        logger.warning("Failed to fetch URL", url=url, error=str(e))
        return None


async def fetch_urls_from_text(text: str, max_urls: int = 3) -> str:
    """Extract URLs from text, fetch content, return combined context string."""
    urls = extract_urls(text)
    if not urls:
        return ""

    contents = []
    for url in urls[:max_urls]:
        content = await fetch_url_content(url)
        if content:
            contents.append(f"[网页内容: {url}]\n{content}")

    return "\n\n".join(contents)
