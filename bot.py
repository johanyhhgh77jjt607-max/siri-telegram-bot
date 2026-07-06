#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════╗
║   🤖 بوت Siri - مساعد Python ذكي متعدد النماذج      ║
║   ملف واحد مستقل | One-File Standalone            ║
║   مع الحماية + التبرع + لوحة تحكم + صلاحيات         ║
╚══════════════════════════════════════════════════╝

التشغيل: python bot.py                    ← Long Polling
        python bot.py --mode webhook       ← Webhook (للخوادم)

الميزات:
  🛡️ Rate Limiter — حماية من تكرار الطلبات
  🔍 Safety Filter — فلترة الكلمات + تصنيف AI
  ⭐ Stars Donation — تبرع بنجوم Telegram
  🎛️ لوحة تحكم /admin — إحصائيات + إدارة
  👥 صلاحيات متعددة — مالك + مشرفين
  💾 تخزين دائم — كل شيء في storage.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الإعداد: pip install python-telegram-bot google-genai groq openai
        عدّل YOUR_TELEGRAM_USER_ID في storage.json إلى ID حسابك
        python bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import json
import logging
import os
import re
import signal
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# ── Telegram ──────────────────────────────────
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, PreCheckoutQueryHandler,
    filters, ContextTypes,
)
from telegram.constants import ParseMode

# ── Gemini ────────────────────────────────────
from google import genai

# ── Groq ──────────────────────────────────────
from groq import AsyncGroq

# ── OpenRouter ────────────────────────────────
from openai import AsyncOpenAI

# ═══════════════════════════════════════════════
# 🔧 الإعدادات
# ═══════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("SiriBot")


def load_config() -> dict:
    config = {
        "telegram_token": "",
        "bot_name": "Yeahsowubot",
        "models": {
            "gemini": {"api_key": "", "model": "gemini-2.0-flash"},
            "groq": {"api_key": "", "model": "llama-3.3-70b-versatile"},
            "openrouter": {
                "api_key": "",
                "base_url": "https://openrouter.ai/api/v1",
                "models": {
                    "gpt4o": "openai/gpt-4o",
                    "claude": "anthropic/claude-3.5-sonnet",
                    "gemini": "google/gemini-2.5-flash",
                },
            },
        },
    }
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            _deep_update(config, json.load(f))
    env_map = {
        "TELEGRAM_TOKEN": ("telegram_token",),
        "TELEGRAM_BOT_TOKEN": ("telegram_token",),
        "BOT_NAME": ("bot_name",),
        "GEMINI_KEY": ("models", "gemini", "api_key"),
        "GEMINI_API_KEY": ("models", "gemini", "api_key"),
        "GROQ_KEY": ("models", "groq", "api_key"),
        "GROQ_API_KEY": ("models", "groq", "api_key"),
        "OPENROUTER_KEY": ("models", "openrouter", "api_key"),
        "OPENROUTER_API_KEY": ("models", "openrouter", "api_key"),
    }
    for env_var, path in env_map.items():
        val = os.environ.get(env_var)
        if val:
            target = config
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = val
    return config


def _deep_update(base: dict, update: dict):
    for k, v in update.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
