from fastapi import APIRouter, Request
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(request: Request):
    from app.services.telegram_bot import process_update

    try:
        data = await request.json()
        await process_update(data)
    except Exception as e:
        logger.error("Telegram webhook error", error=str(e))

    return {"ok": True}
