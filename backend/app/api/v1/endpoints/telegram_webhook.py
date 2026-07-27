import traceback
from fastapi import APIRouter, Request
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(request: Request):
    from app.services.telegram_bot import process_update

    try:
        data = await request.json()
        logger.info("Telegram webhook data received", keys=list(data.keys()))
        await process_update(data)
        logger.info("Telegram webhook processed successfully")
    except Exception as e:
        logger.error("Telegram webhook error", error=str(e), traceback=traceback.format_exc())

    return {"ok": True}
