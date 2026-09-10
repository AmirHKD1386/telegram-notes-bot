<div dir="rtl">

# 🤖 ربات تلگرامی جزوات دانشگاهی

ربات تلگرامی هوشمند برای مدیریت و دسترسی آسان دانشجویان به جزوات و منابع درسی — با اتصال مستقیم به گوگل‌درایو و آمارگیری هوشمند کاربران.

---

## ✨ ویژگی‌ها

- 📁 **نمایش دینامیک فایل‌ها:** هر تغییری در گوگل‌درایو فوری روی ربات بازتاب می‌یابد، بدون نیاز به ری‌استارت
- ☁️ **اتصال ایمن به گوگل درایو:** مدیریت خودکار توکن‌های OAuth2 و رفرش آن‌ها هنگام انقضا
- 🔄 **بازیابی SSL هوشمند:** اگر اتصال SSL به دلیل بیکاری قطع شود، ربات به‌صورت خودکار اتصال را بازسازی می‌کند
- 🔐 **پنل ادمین:** آپلود امن فایل‌های جدید با دستور `/login` و انتخاب پوشه مقصد از طریق Inline Keyboard
- 🚫 **جلوگیری از فایل تکراری:** قبل از آپلود، وجود فایل در پوشه مقصد بررسی می‌شود
- 📊 **آمار هوشمند:** شمارش کاربران یکتا به تفکیک روز (بدون شمردن ادمین)
- 🚀 **معماری Webhook + Flask:** مناسب برای استقرار روی سرورهای ابری

---

## 🛠️ پیش‌نیازها

- Python 3.9+
- اکانت گوگل Cloud با Drive API فعال
- یک سرور یا سرویس هاستینگ با آدرس HTTPS (برای Webhook)

### نصب وابستگی‌ها

```bash
pip install pyTelegramBotAPI flask google-auth google-auth-oauthlib google-api-python-client
```

---

## ⚙️ راه‌اندازی

### ۱. تنظیم متغیرهای محیطی

> ⚠️ **هرگز** توکن و رمزعبور را مستقیماً در کد قرار ندهید.

یک فایل `.env` بسازید:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_PASSWORD=your_secure_password
DRIVE_FOLDER_ID=your_google_drive_folder_id
```

و کد را طوری تنظیم کنید که از `os.getenv()` استفاده کند:

```python
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
```

### ۲. تنظیم گوگل درایو

1. به [Google Cloud Console](https://console.cloud.google.com) بروید
2. یک پروژه جدید بسازید و **Drive API** را فعال کنید
3. یک **OAuth 2.0 Client ID** از نوع Desktop App ایجاد کنید
4. فایل `credentials.json` را دانلود کرده و در کنار `botcode.py` قرار دهید
5. برای تولید `token.json` یک بار احراز هویت را انجام دهید

### ۳. تنظیم Webhook

```bash
# تنظیم وبهوک با توکن ربات و آدرس سرور شما
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://yourdomain.com/<YOUR_TOKEN>"
```

### ۴. اجرا

```bash
python botcode.py
```

---

## 📱 راهنمای دستورات ربات

### دستورات کاربران

| دستور | توضیح |
|-------|-------|
| `/start` | شروع و نمایش خوش‌آمدگویی |
| `/files` | نمایش لیست پوشه‌های درسی |
| `/help` | راهنمای استفاده |
| `/about` | درباره ربات و سازنده |

### دستورات ادمین

| دستور | توضیح |
|-------|-------|
| `/login <password>` | ورود به پنل مدیریت |
| `/logout` | خروج از پنل مدیریت |
| `/stats` | مشاهده آمار کاربران (امروز / کل) |
| ارسال فایل | آپلود جزوه جدید به گوگل‌درایو |

---

## 🏗️ معماری پروژه

```
botcode.py
├── تنظیمات اصلی (BOT_TOKEN, ADMIN_PASSWORD, DRIVE_FOLDER_ID)
├── مدیریت اتصال گوگل درایو (refresh_drive_service, run_drive)
├── آمارگیری هوشمند (increment_usage, get_detailed_stats)
├── پنل ادمین (/login, /logout, /stats, دریافت فایل)
├── نمایش محتوا به کاربران (/files, callback show_)
├── دستورات عمومی (/start, /help, /about)
└── سرور Flask + Webhook
```

---

## 🔒 نکات امنیتی

- ✅ هرگز `token.json` و `credentials.json` را در گیت‌هاب آپلود نکنید — آن‌ها را به `.gitignore` اضافه کنید
- ✅ توکن ربات و رمز ادمین را از طریق متغیرهای محیطی مدیریت کنید
- ✅ فایل `unique_users.txt` را هم به `.gitignore` اضافه کنید

### `.gitignore` پیشنهادی

```gitignore
token.json
credentials.json
unique_users.txt
.env
__pycache__/
*.pyc
```

---

## 👤 سازنده

ساخته شده توسط **AmirHKD** — برای تسهیل دسترسی دانشجویان به منابع درسی.

</div>
