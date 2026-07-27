"""Telegram Bot integration for CEO Agent."""
import base64
import json
import structlog
from io import BytesIO

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from app.core.config import settings
from app.services.model_gateway import get_model_provider, ChatMessage

logger = structlog.get_logger()

_bot_app: Application | None = None


def get_allowed_users() -> set[int]:
    if not settings.TELEGRAM_ALLOWED_USERS:
        return set()
    return {int(uid.strip()) for uid in settings.TELEGRAM_ALLOWED_USERS.split(",") if uid.strip()}


def is_authorized(user_id: int) -> bool:
    allowed = get_allowed_users()
    if not allowed:
        return True  # no restriction if not configured
    return user_id in allowed


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    user = update.effective_user
    logger.info("Telegram /start", user_id=user.id, username=user.username)
    await update.message.reply_text(
        f"你好 {user.first_name}！我是 CEO Agent，你的 AI 经营合伙人。\n\n"
        "你可以：\n"
        "• 发文字 — 讨论经营问题\n"
        "• 发图片 — 让我分析产品、数据截图\n"
        "• /brief — 获取今日经营简报\n"
        "• /help — 查看帮助\n\n"
        f"你的 Telegram ID: {user.id}\n"
        "（首次使用请将此 ID 告知管理员以授权）"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(
        "CEO Agent 命令：\n\n"
        "/start — 开始对话\n"
        "/brief — 今日经营简报\n"
        "/tasks — 查看待办任务\n"
        "/help — 帮助信息\n\n"
        "直接发消息即可对话，支持图片识别。"
    )


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ 未授权，请联系管理员。")
        return

    await update.message.reply_text("正在生成简报...")

    try:
        from app.workers.heartbeat_tasks import _gather_business_context, _call_ai_for_briefing
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.organization import Organization

        async with AsyncSessionLocal() as db:
            orgs = await db.execute(select(Organization))
            org = orgs.scalars().first()
            if not org:
                await update.message.reply_text("暂无数据，请先在 Web 端设置组织信息。")
                return

            ctx = await _gather_business_context(db, org.id)
            summary = await _call_ai_for_briefing(ctx, "morning")
            await update.message.reply_text(f"📊 今日经营简报\n\n{summary}")
    except Exception as e:
        logger.error("Telegram brief failed", error=str(e))
        await update.message.reply_text(f"简报生成失败: {str(e)}")


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ 未授权，请联系管理员。")
        return

    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.task import Task
        from app.models.organization import Organization

        async with AsyncSessionLocal() as db:
            orgs = await db.execute(select(Organization))
            org = orgs.scalars().first()
            if not org:
                await update.message.reply_text("暂无数据。")
                return

            result = await db.execute(
                select(Task).where(
                    Task.organization_id == org.id,
                    Task.status.in_(["pending", "in_progress"]),
                ).order_by(Task.priority.desc()).limit(10)
            )
            tasks = result.scalars().all()
            if not tasks:
                await update.message.reply_text("当前没有进行中的任务。")
                return

            lines = ["📋 当前任务：\n"]
            for t in tasks:
                status_icon = "🔵" if t.status == "in_progress" else "⚪"
                priority_icon = "🔴" if t.priority in ("high", "urgent") else ""
                lines.append(f"{status_icon} {priority_icon}{t.title}")
                if t.due_date:
                    lines.append(f"   截止: {t.due_date}")

            await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error("Telegram tasks failed", error=str(e))
        await update.message.reply_text(f"获取失败: {str(e)}")


async def _get_chat_history(user_id: int, limit: int = 10) -> list[dict]:
    """Get recent chat history from Redis for context."""
    import redis.asyncio as aioredis
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    key = f"tg_history:{user_id}"
    try:
        history = await r.lrange(key, -limit, -1)
        return [json.loads(h) for h in history]
    except Exception:
        return []
    finally:
        await r.aclose()


async def _save_chat_message(user_id: int, role: str, content: str):
    """Save a message to Redis chat history."""
    import redis.asyncio as aioredis
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    key = f"tg_history:{user_id}"
    try:
        await r.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))
        await r.ltrim(key, -50, -1)  # keep last 50 messages
        await r.expire(key, 86400 * 7)  # 7 days TTL
    finally:
        await r.aclose()


async def _build_telegram_context(user_id: int) -> list[ChatMessage]:
    """Build message context including business data and chat history."""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.organization import Organization
    from app.models.memory import Memory
    from app.models.task import Task

    system_prompt = (
        "你是 CEO Agent，一位资深的 AI 经营合伙人。你正在通过 Telegram 与老板对话。\n\n"
        "身份：Aaron USA LLC 的 AI 合伙人，公司经营户外炉灶和厨房用品。\n\n"
        "原则：\n"
        "- 简洁有力，适合手机阅读\n"
        "- 结论前置，必要时展开\n"
        "- 看到产品图片时，分析产品特点、卖点、改进建议\n"
        "- 涉及经营决策时，给出明确建议和风险提示\n"
        "- 记住对话上下文，保持连贯\n"
        "- 用中文回复\n"
    )

    messages = [ChatMessage(role="system", content=system_prompt)]

    try:
        async with AsyncSessionLocal() as db:
            orgs = await db.execute(select(Organization))
            org = orgs.scalars().first()
            if org:
                memories = await db.execute(
                    select(Memory).where(
                        Memory.organization_id == org.id,
                        Memory.status == "confirmed",
                    ).order_by(Memory.importance_score.desc()).limit(10)
                )
                mem_list = memories.scalars().all()
                if mem_list:
                    mem_text = "\n".join([f"- [{m.memory_type}] {m.title}: {m.content}" for m in mem_list])
                    messages.append(ChatMessage(role="system", content=f"长期记忆：\n{mem_text}"))

                tasks_result = await db.execute(
                    select(Task).where(
                        Task.organization_id == org.id,
                        Task.status.in_(["pending", "in_progress"]),
                    ).limit(5)
                )
                task_list = tasks_result.scalars().all()
                if task_list:
                    task_text = "\n".join([f"- [{t.priority}] {t.title}" for t in task_list])
                    messages.append(ChatMessage(role="system", content=f"当前任务：\n{task_text}"))
    except Exception as e:
        logger.warning("Failed to load business context for Telegram", error=str(e))

    history = await _get_chat_history(user_id)
    for h in history:
        messages.append(ChatMessage(role=h["role"], content=h["content"]))

    return messages


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import traceback
    if not update.message or not update.effective_user or not update.message.text:
        logger.warning("Telegram text handler: missing message/user/text")
        return
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ 未授权，请联系管理员。")
        return

    user_id = update.effective_user.id
    user_text = update.message.text
    logger.info("Telegram text message", user_id=user_id, text=user_text[:50])

    await update.message.chat.send_action("typing")
    await _save_chat_message(user_id, "user", user_text)

    try:
        logger.info("Building Telegram context...")
        messages = await _build_telegram_context(user_id)
        messages.append(ChatMessage(role="user", content=user_text))
        logger.info("Calling OpenAI...", message_count=len(messages))

        provider = get_model_provider("openai")
        response = await provider.chat(messages, model="gpt-4o", temperature=0.7, max_tokens=2000)
        reply = response.content
        logger.info("OpenAI response received", length=len(reply))

        await _save_chat_message(user_id, "assistant", reply)

        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)

        logger.info("Telegram reply sent")

    except Exception as e:
        logger.error("Telegram text handler failed", error=str(e), traceback=traceback.format_exc())
        try:
            await update.message.reply_text(f"处理失败: {str(e)}")
        except Exception:
            pass


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ 未授权，请联系管理员。")
        return

    user_id = update.effective_user.id
    caption = update.message.caption or "请分析这张图片"

    await update.message.chat.send_action("typing")

    try:
        photo = update.message.photo[-1]  # highest resolution
        file = await context.bot.get_file(photo.file_id)

        buf = BytesIO()
        await file.download_to_memory(buf)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{b64}"

        await _save_chat_message(user_id, "user", f"[发送了图片] {caption}")

        messages = await _build_telegram_context(user_id)
        messages.append(ChatMessage(role="user", content=caption, image_urls=[data_url]))

        provider = get_model_provider("openai")
        response = await provider.chat(messages, model="gpt-4o", temperature=0.7, max_tokens=2000)
        reply = response.content

        await _save_chat_message(user_id, "assistant", reply)

        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)

    except Exception as e:
        logger.error("Telegram photo handler failed", error=str(e))
        await update.message.reply_text(f"图片处理失败: {str(e)}")


def create_bot_app() -> Application | None:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, Telegram bot disabled")
        return None

    app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("brief", cmd_brief))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

    return app


async def setup_webhook():
    """Set up Telegram webhook on app startup."""
    global _bot_app
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_WEBHOOK_URL:
        return

    _bot_app = create_bot_app()
    if not _bot_app:
        return

    await _bot_app.initialize()
    await _bot_app.bot.set_webhook(
        url=settings.TELEGRAM_WEBHOOK_URL,
        allowed_updates=["message"],
    )
    await _bot_app.start()
    logger.info("Telegram webhook set", url=settings.TELEGRAM_WEBHOOK_URL)


async def shutdown_webhook():
    global _bot_app
    if _bot_app:
        await _bot_app.stop()
        await _bot_app.shutdown()
        _bot_app = None
        logger.info("Telegram bot shutdown")


async def process_update(update_data: dict):
    import traceback
    global _bot_app
    if not _bot_app:
        logger.warning("Telegram bot app not initialized")
        return
    try:
        update = Update.de_json(update_data, _bot_app.bot)
        logger.info("Processing Telegram update", update_id=update.update_id,
                     has_message=bool(update.message),
                     text=update.message.text[:50] if update.message and update.message.text else None)
        await _bot_app.process_update(update)
    except Exception as e:
        logger.error("Telegram process_update error", error=str(e), traceback=traceback.format_exc())
