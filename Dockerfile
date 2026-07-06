FROM python:3.12-slim

WORKDIR /app

# نسخ وتثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# منفذ Koyeb الافتراضي
ENV PORT=8000

# تشغيل البوت بوضع Webhook
CMD ["python", "bot.py", "--mode", "webhook"]
