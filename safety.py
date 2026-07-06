"""
════════════════════
⥑   🛡️ الحماية — RateLimiter + Safety     ║
╚═════════════════════════════════"""
import re
import time
from storage import StorageManager


# SUSPICIOUS_PATTERNS = [
    r"download.*(?:video|vid|mp4|film|movie|serie)",
    r"تحميل.*(?:فيديو|مسلٳل|فيلم|اغنية|اغاني*",
    r"bypass|تجاوز|تخطي",
    r"crack|كراك|باتش",
    r"generate.*(?:password|كلمة.*سر|pass)",
    r"fake|مزيف|مزورة",
    r"free.*(?:premium|stars|نجوم|diamond)",
    r"مجاني.*(?:*بريميوم|نجوم|ماس))",
]


class RateLimiter:
    """يمنع إغراق البوت بالطلبات المتكررة"""
    LIMITS = {
        "/generate": 3,
        "/analyze": 3,
        "/fix": 3,
        "/explain": 8,
        "/optimize": 3,
    }
    WINDOW = 60  # ثانية
    CLEANUP_INTERVAL = 300  # كل 5 دقائق
    def __init__(self, storage: StorageManager):
        self.storage = storage
        self._last_cleanup = time.time()
    def _maybe_cleanup(self):
        now = time.time()
        if now - self._last_cleanup > self.CLEANUP_INTERVAL:
            self.storage.cleanup_rate_limits(self.WINDOW * 2)
            self._last_cleanup = now
    def check(self, user_id: int, command: str) -> dict:
        self._maybe_cleanup()
        limit = self.LIMITS.get(command)
        if limit is None:
            return {"allowed": True, "wait_seconds": 0, "remaining": -1, "reset_in": 0}
        now = time.time()
        user_limits = self.storage.get_rate_limits(user_id)
        timestamps = user_limits.get(command, [])
        timestamps = [ts for ts in timestamps if now - ts < self.WINDOW]
        if len(timestamps) >= limit:
            oldest = min(timestamps)
            wait_seconds = int(self.WINDOW - (now - oldest)) + 1
            return {"allowed": False, "wait_seconds": wait_seconds, "remaining": 0, "reset_in": wait_seconds}
        timestamps.append(now)
        user_limits[command] = timestamps
        self.storage.set_rate_limits(user_id, user_limits)
        return {"allowed": True, "wait_seconds": 0, "remaining": limit - len(timestamps), "reset_in": self.WINDOW}


def check_safety_keywords(text: str, storage: StorageManager) -> tuple:
    text_lower = text.lower()
    all_keywords = storage.get_blocked_keywords()
    for word in all_keywords:
        if word.lower() in text_lower:
            storage.increment_stat("rejected_by_keyword")
            storage.increment_stat("rejected_requests")
            return False, "⚠️ هذا الطلب يحتوي على محتو٩ موالف سياسات الاستخدام."
    return True, ""

def is_suspicious(text: str) -> bool:
    text_lower = text.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

async def check_safety_ai(text: str, groq_client) -> tuple:
    try:
        prompt = (
            "صنف الطلب التالي هل نو طلب برمجي ملدو طلب مخالف "
            "(اختراق، سرقة، محتوى غير قانوني، احتيال)؟\n"
            "أجب بكلمة واحد فقط: SAFE أو UNSAFE\n\n"
            f"الطلب: {text}"
        )
        result = await groq_client.generate(prompt)
        if "UNSAFE" in result.upper():
            return False, "⚠️ تم رفض الطلب — يخالف سياسات الاستخدام."
        return True, ""
    except Exception:
        return True, ""
