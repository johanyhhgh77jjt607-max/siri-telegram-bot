# 🤖 بوت Siri - مساعد Python ذكي على Telegram

بوت Telegram متعدد النماذج للساعدة المبرمجين في كتابة وتحليل وتصحيح أكواد Python.

## ✨ الميزات

- 🧠 **توليد الأكواد** — GPT-4o + Gemini + مراجعة Claude
- 🔍 **تحليل الأكواد** — من 3 زوايا (Claude + GPT-4o + Gemini)
- 🔧 **تصحيح الأخطاء** — GPT-4o يصحح + Claude يراجع + Gemini يتحقق
- 📖 **شرح الأكواد** — شرح مفصل بالعربية عبر Groq
- ⚡ **تحسين الأداء** — GPT-4o + Groq
- 🛡️ **حماية** — Rate Limiter + Safety Filter
- ⭐ **تبرع** — Telegram Stars
- 🎛️ **لوحة تحكم** — `/admin` + صلاحيات متعددة
- 💾 **تخزين دائم** — storage.json

## 🚀 النشر على Koyeb

1. انسخ `config.example.json` → `config.json` واملأ المفاتيح
2. ارفع على [Koyeb](https://koyeb.com)
3. أضف متغيرات البيئة: `TELEGRAM_TOKEN`, `GEMINI_KEY`, `GROQ_KEY`, `OPENROUTER_KEY`
4. انشر!

## ⚙️ تشغيل محلي

```bash
pip install -r requirements.txt
cp config.example.json config.json
python bot.py
```

## 📋 الأوامر

| الأمر | الوصف |
|-------|-------|
| `/start` | ترحيب |
| `/generate وصف` | توليد كود |
| `/analyze` | تحليل |
| `/fix` | تصحيح |
| `/explain` | شرح |
| `/optimize` | تحسين |
| `/donate` | تبرع |
| `/admin` | لوحة تحكم |

## 🧠 النماذج

GPT-4o · Claude 3.5 · Gemini 2.0 · Llama 3.3
