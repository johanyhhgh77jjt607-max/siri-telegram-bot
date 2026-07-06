"""
╔══════════════════════════════════════════╗
║   📨 معالجات الأوامر الأساسية             ║
╚══════════════════════════════════════════╝
"""
from typing import Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from models import ModelAggregator
from storage import StorageManager
from safety import RateLimiter, check_safety_keywords, is_suspicious, check_safety_ai
from utils import (extract_code_from_message, extract_code_and_error, extract_after_command, send_long_message)

HELP_TEXT = """🤖 **بوت Siri - مساعد Python الذكي متعدد النماذج**

📌 **الأوامر البرمجية:**
RELP reduced for brevity

class BotHandlers:
    def __init__(self, aggregator, storage, bot_name="Yeahsowubot"):
        self.agg = aggregator
        self.storage = storage
        self.bot_name = bot_name
        self.rate_limiter = RateLimiter(storage)
        self._awaiting: Dict[int, str] = {}

    async def _check_access(self, update, command):
        user = update.message.from_user
        if self.storage.is_banned(user.id):
            return False, "🚫 أنت محظور من استخدام البوت."
        rl = self.rate_limiter.check(user.id, command)
        if not rl["allowed"]:
            self.storage.increment_stat("rejected_by_ratelimit")
            return False, f"⟳ **تمهل قليلاً!**\n혭 اول مري أخرى بعد {rl['wait_seconds']} ثانية"
        self.storage.increment_stat("total_requests")
        return True, ""

    def _has_permission(self, user_id, flag):
        if self.storage.is_owner(user_id): return True
        return self.storage.get_admin_flags(user_id).get(flag, False)

    async def _start(self, update, context):
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ دعم البوت", callback_data="donate_menu")], [InlineKeyboardButton("📖 /help", callback_data="cmd_help")]])
        await update.message.reply_text(START_TEXT, parse_mode="Markdown", reply_markup=kb)

    async def _help(self, update, context):
        await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")

    async def _generate(self, update, context):
        ok, msg = await self._check_access(update, "/generate")
        if not ok: await update.message.reply_text(msg); return
        prompt = extract_after_command(update.message.text, "generate", self.bot_name)
        if not prompt:
            await update.message.reply_text("⚠️ أرسل وصفاً للكود"); return
        status = await update.message.reply_text("⏳ جاري توليد")
        if is_suspicious(prompt):
            safe, reason = await check_safety_ai(prompt, self.agg.groq)
            if not safe:
                self.storage.increment_stat("rejected_by_ai")
                await status.edit_text(reason); return
        result = await self.agg.generate_code(prompt)
        await send_long_message(update, status, result)

    async def _analyze(self, update, context):
        ok, msg = await self._check_access(update, "/analyze")
        if not ok: await update.message.reply_text(msg); return
        code = extract_code_from_message(update.message)
        if not code:
            await update.message.reply_text("⚠️ أرسل الكود"); return
        status = await update.message.reply_text("🔍 جاري التحليل")
        result = await self.agg.analyze_code(code)
        await send_long_message(update, status, result)

    async def _fix(self, update, context):
        ok, msg = await self._check_access(update, "/fix")
        if not ok: await update.message.reply_text(msg); return
        code, error = extract_code_and_error(update.message)
        if not code:
            await update.message.reply_text("⚠️ أرسل الكود + خطأ"); return
        status = await update.message.reply_text("🔧 جاري التصحيح")
        result = await self.agg.fix_code(code, error)
        await send_long_message(update, status, result)

    async def _explain(self, update, context):
        ok, msg = await self._check_access(update, "/explain")
        if not ok: await update.message.reply_text(msg); return
        code = extract_code_from_message(update.message)
        if not code:
            await update.message.reply_text("⚠️ أرسل الكود"); return
        status = await update.message.reply_text("📖 جاري شرح الكود ⚡")
        result = await self.agg.explain_code(code)
        await send_long_message(update, status, result)

    async def _optimize(self, update, context):
        ok, msg = await self._check_access(update, "/optimize")
        if not ok: await update.message.reply_text(msg); return
        code = extract_code_from_message(update.message)
        if not code:
            await update.message.reply_text("⚠️ أرسل الكود"); return
        status = await update.message.reply_text("⚡ جاري التحسين")
        result = await self.agg.optimize_code(code)
        await send_long_message(update, status, result)

    async def _donate(self, update, context):
        self.storage.increment_stat("total_requests")
        self.storage.increment_stat("cmd:/donate")
        await self._show_donate_menu(update.message.chat_id, is_new=True, message=update.message)

    async def _show_donate_menu(self, chat_id, is_new=True, message=None):
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐50", callback_data="donate_50"), InlineKeyboardButton("⭐100", callback_data="donate_100"), InlineKeyboardButton("⭐250", callback_data="donate_250")], [InlineKeyboardButton("⭐500", callback_data="donate_500"), InlineKeyboardButton("⭐1000", callback_data="donate_1000")], [InlineKeyboardButton("✏️ مبلغ مخصص", callback_data="donate_custom")], [InlineKeyboardButton("📊 إحصائيات التبرعات", callback_data="donate_stats")]])
        text = "⭐ **ادعم بوت Siri**\nدعم لسرقم للتبرع بها\nسكراً لكل الداعم!"
        if is_new and message: await message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
        else: await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _donate_callback(self, update, context):
        query = update.callback_query; await query.answer()
        data = query.data; user = update.effective_user
        if data == "donate_stats":
            ds = self.storage.get_donation_stats()
            await query.edit_message_text(f"📊 إصائيات التبرعات\n⭐ مجموع: {ds['total_stars']}\n👥 عدد المتبرعين: {ds['total_donors']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="donate_menu")]]))
            return
        if data == "donate_custom":
            self._awaiting[user.id] = "donation_amount"
            await query.edit_message_text("✏️ كم نجمة تريد التبرع أرسل الرقم (A-2500)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="donate_menu")]]))
            return
        if data == "donate_menu":
            await self._show_donate_menu(update.effective_chat.id, is_new=False, message=query.message)
            return
        if data.startswith("donate_"):
            try:
                amount = int(data.split("_")[1])
                await query.message.delete()
                await self._send_stars_invoice(update.effective_chat.id, amount, context)
            except: pass

    async def _send_stars_invoice(self, chat_id, amount, context):
        await context.bot.send_invoice(chat_id=chat_id, title="⭐ دعم بوت Siri", description=f"تبرع بـ {amount} نجمة", payload=f"donation_{amount}", provider_token="", currency="XTR", prices=[LabeledPrice(f"تبرع {amount}⭐", amount)], start_parameter="donate")

    async def _handle_custom_donation(self, update, context):
        user_id = update.message.from_user.id
        if self._awaiting.get(user_id) != "donation_amount": return
        self._awaiting.pop(user_id, None)
        try:
            amount = int(update.message.text.strip())
            if 1 <= amount <= 2500:
                await self._send_stars_invoice(update.message.chat_id, amount, context)
            else: await update.message.reply_text("⚠️ الرجاء إدخال رقم بين 1 و 2500")
        except ValueError: await update.message.reply_text("⚠️ الرجاء إدخال رقم ص٭يح")

    async def _pre_checkout(self, update, context): await update.pre_checkout_query.answer(ok=True)

    async def _successful_payment(self, update, context):
        payment = update.message.successful_payment
        user = update.message.from_user
        self.storage.add_donation(user_id=user.id, username=user.username or "بدون معرف", full_name=user.full_name, amount=payment.total_amount, tx_id=payment.telegram_payment_charge_id)
        await update.message.reply_text(f"🎉 **شكراً جزيلاً {user.full_name}!**\nلقد تبرعت بـ ⭐**{payment.total_amount}** نجمة.", parse_mode="Markdown")

    async def _handle_message(self, update, context):
        user_id = update.message.from_user.id
        awaiting = self._awaiting.get(user_id)
        if awaiting:
            if awaiting == "donation_amount":
                await self._handle_custom_donation(update, context); return
            from admin_handlers import AdminHandlers
            admin = AdminHandlers(self)
            if awaiting.startswith("admin_kw_add_"): await admin._handle_admin_kw_input(update, context); return
            elif awaiting == "admin_ban_add": await admin._handle_admin_ban_input(update, context); return
            elif awaiting == "admin_adm_add": await admin._handle_admin_adm_input(update, context); return
        text = update.message.text or ""
        if text.startswith("/"):
            await update.message.reply_text("❓ أمر غير معروف. استخدم /help."); return
        code = extract_code_from_message(update.message)
        if code:
            await update.message.reply_text("👀 **رأيت أنك أرسلت كود Python!**\nماذا تريد أن أفعل به؟\n\n🔍 /analyze | 🔧 /fix | 📖 /explain | ⚡ /optimize", parse_mode="Markdown")

START_TEXT = """👋 **مرحباً! أنا بوت Siri** 🐍دعم Python محترف بسوه 4 نماذج: GPT-4o | Claude 3.5 | Gemini | Groq استخدم /help لمعرفة جميع الأوامر!"💡 جرب الآن: `/generate لعبة تخمين الأرقام`"""