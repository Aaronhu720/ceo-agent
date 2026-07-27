from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.api.v1.router import api_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CEO Agent API", env=settings.APP_ENV)

    from app.services.storage_service import storage_service
    try:
        storage_service.ensure_bucket()
        logger.info("Storage bucket verified")
    except Exception as e:
        logger.warning("Storage bucket check failed (MinIO may not be ready)", error=str(e))

    from app.services.telegram_bot import setup_webhook, shutdown_webhook
    try:
        await setup_webhook()
    except Exception as e:
        logger.warning("Telegram bot setup failed", error=str(e))

    yield

    try:
        await shutdown_webhook()
    except Exception as e:
        logger.warning("Telegram bot shutdown failed", error=str(e))

    logger.info("Shutting down CEO Agent API")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc) if settings.DEBUG else None},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request", method=request.method, path=request.url.path)
    response = await call_next(request)
    return response


app.include_router(api_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": "0.1.0"}


# ML notification webhook alias (matches URL configured in ML developer console)
@app.post("/api/integrations/mercadolibre/webhook")
async def ml_webhook_alias(request: Request):
    import logging
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    logging.getLogger(__name__).info("ML webhook notification: %s", body)
    return {"status": "ok"}
