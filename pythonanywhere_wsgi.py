"""
╔══════════════════════════════════════════╗
║   🐍 PythonAnywhere WSGI Entry Point    ║
║   لاستضافة بوت Siri مجاناً               ║
╚══════════════════════════════════════════╝
"""
import asyncio
import json
import logging
import os
import sys

# إضافة مسار البوت
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SiriBot-PA")

from config import load_config
from storage import StorageManager
from models import ModelAggregator
from handlers import BotHandlers
from admin_handlers import AdminHandlers
from telegram import Update
from telegram.ext import Application

_initialized = False
_application = None
_storage = None


def _init():
    global _initialized, _application, _storage
    if _initialized:
        return

    config = load_config()
    token = config["telegram_token"]

    if not token:
        raise RuntimeError("❌ Telegram token مفقود!")

    aggregator = ModelAggregator(config)
    _storage = StorageManager()
    bot_handlers = BotHandlers(aggregator, _storage, config.get("bot_name", "Yeahsowubot"))
    admin = AdminHandlers(bot_handlers)

    _application = Application.builder().token(token).build()

    from bot import register_handlers
    register_handlers(_application, bot_handlers, admin)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_application.initialize())
    loop.run_until_complete(_application.start())

    webhook_url = os.environ.get("WEBHOOK_URL", "")
    if webhook_url:
        loop.run_until_complete(
            _application.bot.set_webhook(url=f"{webhook_url.rstrip('/')}/webhook")
        )
        logger.info(f"🔗 Webhook set: {webhook_url}/webhook")

    _initialized = True
    logger.info("✅ البوت جاهز!")


def application(environ, start_response):
    """WSGI entry point لـ PythonAnywhere"""
    _init()

    request_path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    # Webhook endpoint
    if method == "POST" and request_path == "/webhook":
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            body = environ["wsgi.input"].read(content_length)
            data = json.loads(body)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            update = Update.de_json(data, _application.bot)
            loop.run_until_complete(_application.process_update(update))

            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"OK"]
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            start_response("500 Error", [("Content-Type", "text/plain")])
            return [str(e).encode()]

    # Health check
    start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
    return ["🤖 بوت Siri شغال! ✅".encode("utf-8")]
