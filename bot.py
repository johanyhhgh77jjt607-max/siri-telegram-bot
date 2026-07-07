#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════╗
║   🤖 بوت Siri - مساعد Python ذكي متعدد النماذج      ║
║   GPT-4o | Claude 3.5 | Gemini | Groq           ║
║   🛡️ حماية | ⭐ تبرع | 🎛️ لوحة تحكم | 👥 صلاحيات  ║
╚══════════════════════════════════════════════════╝

التشغيل: python bot.py                    ← Long Polling
        python bot.py --mode webhook       ← Webhook (للخوادم)
"""
import asyncio
import logging
import os
import signal
import sys

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, PreCheckoutQueryHandler,
    filters,
)

from config import load_config
from storage import StorageManager
from models import ModelAggregator
from handlers import BotHandlers
from admin_handlers import AdminHandlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("SiriBot")

BANNER = """
╔══════════════════════════════════════════════════╗
║   🤖 بوت Siri - مساعد Python ذكي متعدد النماذج      ║
║   GPT-4o | Claude 3.5 | Gemini | Groq           ║
║   🛡️ حماية | ⭐ تبرع | 🎛️ لوحة تحكم | 👥 صلاحيات  ║
╚══════════════════════════════════════════════════╝
"""


def register_handlers(application, handlers, admin):
    """تسجيل جميع معالجات الأوامر"""
    # الأوامر الأساسية
    application.add_handler(CommandHandler("start", handlers._start))
    application.add_handler(CommandHandler("help", handlers._help))
    application.add_handler(CommandHandler("generate", handlers._generate))
    application.add_handler(CommandHandler("analyze", handlers._analyze))
    application.add_handler(CommandHandler("fix", handlers._fix))
    application.add_handler(CommandHandler("explain", handlers._explain))
    application.add_handler(CommandHandler("optimize", handlers._optimize))
    # التبرع
    application.add_handler(CommandHandler("donate", handlers._donate))
    # لوحة التحكم والصلاحيات (AdminHandlers)
    application.add_handler(CommandHandler("admin", admin._admin))
    application.add_handler(CommandHandler("promote", admin._promote))
    application.add_handler(CommandHandler("demote", admin._demote))
    application.add_handler(CommandHandler("permissions", admin._permissions))
    application.add_handler(CommandHandler("ban", admin._ban))
    application.add_handler(CommandHandler("unban", admin._unban))
    application.add_handler(CommandHandler("addword", admin._addword))
    application.add_handler(CommandHandler("delword", admin._delword))
    application.add_handler(CommandHandler("stats", admin._stats))
    # Callback handlers
    application.add_handler(CallbackQueryHandler(handlers._donate_callback, pattern=r"^donate_"))
    application.add_handler(CallbackQueryHandler(admin._admin_callback, pattern=r"^admin_"))
    application.add_handler(CallbackQueryHandler(admin._demote_callback, pattern=r"^demote_"))
    application.add_handler(CallbackQueryHandler(handlers._donate_callback, pattern=r"^cmd_help"))
    # Stars payment
    application.add_handler(PreCheckoutQueryHandler(handlers._pre_checkout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handlers._successful_payment))
    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers._handle_message))


async def run_polling(config: dict, duration: int = 110):
    token = config["telegram_token"]
    bot_name = config.get("bot_name", "Yeahsowubot")
    print(BANNER)
    print(f"⏱️  مدة الجلسة: {duration}s | الوضع: Polling")
    print("🧠 جاري تهيئة النماذج...")
    aggregator = ModelAggregator(config)
    print("✅ GPT-4o | Claude 3.5 | Gemini | Groq - جاهزون!")
    storage = StorageManager()
    print(f"💾 التخزين: {storage.path}")
    handlers = BotHandlers(aggregator, storage, bot_name)
    admin = AdminHandlers(handlers)
    application = Application.builder().token(token).build()
    register_handlers(application, handlers, admin)
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()
    loop.call_later(duration, lambda: stop_event.set())
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: stop_event.set())
        except NotImplementedError:
            pass
    print(f"🚀 البوت يعمل! @{bot_name}")
    print("📋 /start | /generate | /analyze | /fix | /explain | /optimize | /donate | /admin")
    print(f"⌛ انتظار الرسائل... (إيقاف تلقائي بعد {duration}s)\n")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    await stop_event.wait()
    logger.info("🛑 جاري إيقاف البوت...")
    storage.save()
    logger.info("💾 تم حفظ التخزين.")
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    logger.info("✅ تم إيقاف البوت.")


# ═══════════════════════════════════════════════
# 🖥️ وضع Webhook
# ═══════════════════════════════════════════════

try:
    from aiohttp import web as aiohttp_web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


async def run_webhook(config: dict):
    if not HAS_AIOHTTP:
        print("❌ وضع webhook يحتاج aiohttp: pip install aiohttp")
        return
    token = config["telegram_token"]
    bot_name = config.get("bot_name", "Yeahsowubot")
    port = int(os.environ.get("PORT", 8000))
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    print(BANNER)
    print(f"🌐 Webhook | المنفذ: {port}")
    aggregator = ModelAggregator(config)
    storage = StorageManager()
    handlers = BotHandlers(aggregator, storage, bot_name)
    admin = AdminHandlers(handlers)
    application = Application.builder().token(token).build()
    register_handlers(application, handlers, admin)
    await application.initialize()
    await application.start()

    async def webhook_endpoint(request):
        try:
            data = await request.json()
            update = Update.de_json(data, application.bot)
            await application.process_update(update)
            return aiohttp_web.Response(text="OK")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return aiohttp_web.Response(text="Error", status=500)

    async def health_check(request):
        return aiohttp_web.Response(text="Bot is alive! ✅")

    app = aiohttp_web.Application()
    app.router.add_post("/webhook", webhook_endpoint)
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    if webhook_url:
        webhook_path = f"{webhook_url.rstrip('/')}/webhook"
        await application.bot.set_webhook(url=webhook_path)
        print(f"🔗 Webhook: {webhook_path}")
    print(f"🌐 الخادم: المنفذ {port}")
    print(f"🚀 @{bot_name} جاهز!\n")
    runner = aiohttp_web.AppRunner(app)
    await runner.setup()
    site = aiohttp_web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_event_loop().add_signal_handler(sig, lambda: stop_event.set())
        except NotImplementedError:
            pass
    await stop_event.wait()
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    storage.save()


# ═══════════════════════════════════════════════
# 🎯 الدخول
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    config = load_config()
    if not config["telegram_token"]:
        print("❌ التوكن مفقود! ضعه في config.json أو TELEGRAM_TOKEN")
        sys.exit(1)
    mode = "polling"
    duration = 110
    no_stop = False
    for i, arg in enumerate(sys.argv):
        if arg == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1]
        if arg.startswith("--duration="):
            duration = int(arg.split("=")[1])
        if arg == "--no-stop":
            no_stop = True
    if no_stop:
        duration = 86400 * 365
    if mode == "webhook":
        asyncio.run(run_webhook(config))
    else:
        asyncio.run(run_polling(config, duration))
