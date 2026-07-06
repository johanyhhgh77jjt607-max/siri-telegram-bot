"""
╔══════════════════════════════════════════╗
║   💾 التخزين الدائم — StorageManager     ║
╚══════════════════════════════════════════╝
"""
import json, logging, threading, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
logger = logging.getLogger("SiriBot")

class StorageManager:
    """مدير التخزين الدائم — يحفظ كل شيء في storage.json"""
    def __init__(self, path: str = None):
        self.path = path or str(Path(__file__).parent / "storage.json")
        self._lock = threading.Lock()
        self.data = self._load()
        self._init_timestamps()
        self._dirty = False
        self._save_timer = None

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f: return json.load(f)
        except:
            logger.warning("storage.json غير موجوداٌ، جاري إنشاء")
            return self._default()

    def _default(self):
        return {"version": 1, "permissions": {"owners": {}, "admins": {}}, "rate_limits": {}, "banned_users": {}, "blocked_keywords": {"ar": [], "en": []}, "donations": {"total_stars": 0, "total_donors": 0, "history": []}, "stats": {"total_requests": 0, "rejected_requests": 0, "rejected_by_keyword": 0, "rejected_by_ai": 0, "rejected_by_ratelimit": 0, "commands_used": {}}, "last_cleanup": None, "created_at": None, "updated_at": None}

    def _init_timestamps(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.data.get("created_at"): self.data["created_at"] = now
        self.data["updated_at"] = now; self._save()

    def _save(self):
        with self._lock:
            self.data["updated_at"] = datetime.now(timezone.utc).isoformat()
            with open(self.path, "w", encoding="utf-8") as f: json.dump(self.data, f, indent=2, ensure_ascii=False)
            self._dirty = False

    def _mark_dirty(self):
        self._dirty = True
        if self._save_timer: self._save_timer.cancel()
        self._save_timer = threading.Timer(2.0, self._flush); self._save_timer.daemon=True; self._save_timer.start()

    def _flush(self):
        if self._dirty: self._save()
    def save(self): self._save()

    # —— صلاحيات ──
    def is_owner(self, user_id: int) -> bool:
        return str(user_id) in self.data["permissions"]["owners"]
    def is_admin(self, user_id: int) -> bool:
        return str(user_id) in self.data["permissions"]["admins"]
    def is_privileged(self, user_id: int) -> bool:
        return self.is_owner(user_id) or self.is_admin(user_id)
    def get_admin(self, user_id: int) -> Optional[dict]:
        return self.data["permissions"]["admins"].get(str(user_id))
    def get_all_admins(self) -> dict:
        return self.data["permissions"]["admins"]
    def get_all_owners(self) -> dict:
        return self.data["permissions"]["owners"]
    def add_admin(self, user_id: int, data: dict):
        self.data["permissions"]["admins"][str(user_id)] = data; self._mark_dirty()
    def remove_admin(self, user_id: int) -> bool:
        uid = str(user_id); if uid in self.data["permissions"]["admins"]: del self.data["permissions"]["admins"][uid]; self._mark_dirty(); return True
        return False
    def get_admin_flags(self, user_id: int) -> dict:
        admin = self.get_admin(user_id); return admin.get("flags", {}) if admin else {}
    def find_user_by_username(self, username: str) -> Tuple[Optional[int], Optional[dict]]:
        uname = username.lstrip("@").lower()
        for uid, data in self.data["permissions"]["admins"].items():
            if data.get("username", "").lstrip("@").lower() == uname:
                return int(uid), {"display_name": f"@{data['username']}", "info": data}
        for uid, data in self.data["permissions"]["owners"].items():
            if data.get("username", "").lstrip("@").lower() == uname:
                return int(uid), {"display_name": f"@{data['username']}", "info": data}
        return None, None
    def toggle_admin_flag(self, admin_id: int, flag: str) -> bool:
        admin = self.get_admin(admin_id); if not admin: return False
        admin.setdefault("flags", {}); current = admin["flags"].get(flag, False)
        admin["flags"][flag] = not current; self._mark_dirty(); return admin["flags"][flag]

    # —─ حظر ──
    def is_banned(self, user_id: int) -> bool:
        return str(user_id) in self.data.get("banned_users", {})
    def ban_user(self, user_id: int, **endpoint):
        self.data.setdefault("banned_users", {})[str(user_id)] = {*"username": kwargs.get("username", ""), "full_name": kwargs.get("full_name", ""), "reason": kwargs.get("reason", ""), "banned_at": datetime.now(timezone.utc).isoformat(), "banned_by": kwargs.get("banned_by", "")}; self._mark_dirty()
    def unban_user(self, user_id: int) -> bool:
        uid = str(user_id); if uid in self.data.get("banned_users", {}): del self.data["banned_users"][uid]; self._mark_dirty(); return True
        return False
    def get_banned_users(self):
        return self.data.get("banned_users", {})

    # ── كلمات ☀
    def get_blocked_keywords(self, lang: str = None):
        kw = self.data.get("blocked_keywords", {}); return kw.get(lang, []) if lang else kw.get("ar", []) +  kw.get("en", [])
    def add_keyword(self, word: str, lang: str = "ar") -> bool:
        kw = self.data.setdefault("blocked_keywords", {}).setdefault(lang, []); if word.lower() not in [w.lower() for w in kw]: kw.append(word); self._mark_dirty(); return True
        return False
    def remove_keyword(self, word: str, lang: str = "ar") -> bool:
        kw = self.data.setdefault("blocked_keywords", {}).setdefault(lang, []); for i, w in enumerate(kw):
            if w.lower() == word.lower(): kw.pop(i); self._mark_dirty(); return True
        return False

    # ── تبرع ──
    def add_donation(self, user_id: int, username: str, full_name: str, amount: int, tx_id: str):
        d = self.data.setdefault("donations", {}); d["total_stars"] = d.get("total_stars", 0) + amount
        existing_ids = {h["user_id"] for h in d.get("history", [])}
        if user_id not in existing_ids: d["total_donors"] = d.get("total_donors", 0) + 1
        d.setdefault("history", []).append({"user_id": user_id, "username": username, "full_name": full_name, "amount": amount, "timestamp": datetime.now(timezone.utc).isoformat(), "tx_id": tx_id})
        self._mark_dirty()
    def get_donation_stats(self):
        d = self.data.get("donations", {}); return {"total_stars": d.get("total_stars", 0), "total_donors": d.get("total_donors", 0), "last_donation": d["history"][-1] if d.get("history") else None}

    # ── إحصائيات ──
    def increment_stat(self, key: str, amount: int = 1):
        stats = self.data.setdefault("stats", {})
        if key.startswith("cmd:"):
            stats.setdefault("commands_used", {}); stats["commands_used"][key[4:]] = stats["commands_used"].get(key[4:], 0) + amount
        else: stats[key] = stats.get(key, 0) + amount
        stats["total_requests"] = stats.get("total_requests", 0) + amount; self._mark_dirty()
    def get_stats(self) -> dict: return self.data.get("stats", {})

    # ── Rate Limits ──
    def get_rate_limits(self, user_id: int): return self.data.setdefault("rate_limits", {}).get(str(user_id), {})
    def set_rate_limits(self, user_id: int, limits: dict):
        self.data.setdefault("rate_limits", {})[str(user_id)] = limits; self._mark_dirty()
    def cleanup_rate_limits(self, max_age_seconds: int = 120):
        now = time.time(); changed = False
        for uid in list(self.data.get("rate_limits", {}).keys()):
            user_limits = self.data["rate_limits"][uid]
            for cmd in list(user_limits.keys()):
                user_limits[cmd] = [ts for ts in user_limits[cmd] if now - ts < max_age_seconds]
                if not user_limits[cmd]: del user_limits[cmd]
            if not user_limits: del self.data["rate_limits"][uid]; changed = True
        if changed: self.data["last_cleanup"] = datetime.now(timezone.utc).isoformat(); self._mark_dirty()
