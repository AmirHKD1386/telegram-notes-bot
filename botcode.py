import io
import os
import telebot
from flask import Flask, request
from telebot import apihelper
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

apihelper.proxy = {'https': 'http://proxy.server:3128'}

# ================== تنظیمات اصلی ربات ==================
BOT_TOKEN = '8550656921:AAFWL3rWvP4sTbrpvkjWYEDr_k0YZ6eeV8w'
ADMIN_PASSWORD = 'amIr138619'
DRIVE_FOLDER_ID = '1Vd04HROCH7ijcAXGnE28RvdjoCe9hQ6E'

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

# ================== تنظیمات آمارگیر ربات ==================
COUNTER_FILE = os.path.join(BASE_DIR, 'unique_users.txt')
ADMIN_CHAT_ID = 691242717  # ⚠️ آیدی عددی تلگرام خودت را اینجا بنویس تا آمار خودت شمرده نشود

def increment_usage(chat_id):
    """ذخیره آیدی کاربر برای محاسبه آمار بدون تکرار"""
    if chat_id in authenticated_admins or chat_id == ADMIN_CHAT_ID:
        return
    
    existing_users = set()
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            existing_users = set(line.strip() for line in f if line.strip())
            
    if str(chat_id) not in existing_users:
        with open(COUNTER_FILE, 'a') as f:
            f.write(f"{chat_id}\n")

def get_usage_count():
    """محاسبه تعداد کل کاربران منحصربه‌فرد بر اساس تعداد خطوط فایل"""
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            return len(lines)
    return 0

# ================== مدیریت هوشمند اتصال گوگل درایو ==================
drive_service = None

def refresh_drive_service():
    """تابع مرکزی برای ساخت و نوسازی اتصال گوگل درایو"""
    global drive_service
    try:
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

            # رفرش خودکار توکن منقضی شده در صورت لزوم
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                except Exception as refresh_error:
                    print(f"⚠️ خطای موقت در رفرش توکن: {refresh_error}")

            drive_service = build('drive', 'v3', credentials=creds)
            print("✅ اتصال امن به گوگل درایو برقرار/نوسازی شد.")
        else:
            print("❌ فایل token.json یافت نشد!")
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی اولیه گوگل درایو: {e}")

# اجرای اولیه اتصال در زمان استارت آپ سرور
refresh_drive_service()

def run_drive(action):
    """
    واسط هوشمند برای اجرای دستورات درایو. 
    اگر پروتکل SSL به دلیل بیکاری قطع شده باشد، آن را درجا نوسازی می‌کند.
    """
    global drive_service
    try:
        return action(drive_service)
    except Exception as e:
        if "EOF occurred in violation of protocol" in str(e):
            print("⚠️ تداخل یا انقضای پروتکل SSL رخ داد. در حال نوسازی خودکار...")
            refresh_drive_service()
            return action(drive_service)  # تلاش مجدد با کانکشن جدید
        raise e

authenticated_admins = set()
pending_files = {}

# ================== مدیریت ورود ادمین ==================
@bot.message_handler(commands=['login'])
def admin_login(message):
    entered_password = message.text.replace('/login', '').strip()
    if entered_password == ADMIN_PASSWORD:
        authenticated_admins.add(message.chat.id)
        bot.reply_to(message, "🔓 ورود موفقیت‌آمیز بود ادمین گرامی! اکنون می‌توانید فایل جزوه را فرستاده تا ربات بپرسد در کدام پوشه ذخیره شود.")
    else:
        bot.reply_to(message, "❌ دستور نامعتبر است.")

@bot.message_handler(commands=['logout'])
def admin_logout(message):
    if message.chat.id in authenticated_admins:
        authenticated_admins.remove(message.chat.id)
        bot.reply_to(message, "🔒 با موفقیت از پنل مدیریت خارج شدید.")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.chat.id not in authenticated_admins:
        return
        
    current_count = get_usage_count()
    bot.reply_to(
        message, 
        f"📊 **آمار عملکرد ربات جزوات:**\n\n"
        f"👥 تعداد کل دانشجویان (کاربران یکتا): **{current_count}** نفر",
        parse_mode="Markdown"
    )

# ================== آپلود فایل توسط ادمین ==================
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.chat.id not in authenticated_admins:
        return

    if not drive_service:
        bot.reply_to(message, "❌ ارتباط با گوگل درایو برقرار نیست (فایل token.json را بررسی کنید).")
        return

    pending_files[message.chat.id] = message.document

    try:
        results = run_drive(lambda service: service.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)"
        ).execute())
        folders = results.get('files', [])

        if not folders:
            bot.reply_to(message, "❌ هیچ پوشه‌ای یافت نشد! شناسه پوشه اصلی در کدت را بررسی کن.")
            return

        markup = telebot.types.InlineKeyboardMarkup()
        buttons = [telebot.types.InlineKeyboardButton(text=f"📁 {f['name']}", callback_data=f"cat_{f['id']}") for f in folders]

        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])

        bot.reply_to(message, "📥 فایل دریافت شد. این فایل جزوه در کدام پوشه درسی ذخیره شود؟", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"❌ خطا در خواندن پوشه‌ها: {str(e)}")

def escape_markdown(text):
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def callback_admin_category(call):
    chat_id = call.message.chat.id
    if chat_id not in pending_files:
        bot.answer_callback_query(call.id, "❌ فایل یافت نشد.")
        return

    target_folder_id = call.data.replace('cat_', '')
    document = pending_files[chat_id]
    del pending_files[chat_id]

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="⏳ در حال بررسی فایل...")

    try:
        existing_files = run_drive(lambda service: service.files().list(
            q=f"'{target_folder_id}' in parents and name='{document.file_name}' and trashed=false",
            fields="files(id, name)"
        ).execute()).get('files', [])

        if existing_files:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
            text=f"⚠️ فایل **{escape_markdown(document.file_name)}** قبلاً در این پوشه آپلود شده است",
            parse_mode="MarkdownV2")
            return

        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="⏳ در حال آپلود...")

        file_info = bot.get_file(document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_metadata = {
            'name': document.file_name,
            'parents': [target_folder_id]
        }
        media = MediaIoBaseUpload(io.BytesIO(downloaded_file), mimetype=document.mime_type, resumable=True)

        uploaded_file = run_drive(lambda service: service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute())

        try:
            run_drive(lambda service: service.permissions().create(
                fileId=uploaded_file.get('id'),
                body={'type': 'anyone', 'role': 'reader'}
            ).execute())
        except: pass

        safe_name = escape_markdown(document.file_name)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"✅ فایل **{safe_name}** با موفقیت ذخیره شد\n🔗 [لینک دانلود]({uploaded_file.get('webViewLink')})",
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطایی رخ داد:\n{str(e)}")

# ================== بخش نمایش منو و پوشه‌ها به کاربران ==================
@bot.message_handler(commands=['files'])
def list_files(message):
    increment_usage(message.chat.id)  # 👈 ثبت هوشمند کاربر یکتا در اینجا
    
    if not drive_service:
        bot.reply_to(message, "❌ ارتباط با گوگل درایو برقرار نیست (فایل token.json را بررسی کنید).")
        return
    try:
        results = run_drive(lambda service: service.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)"
        ).execute())
        folders = results.get('files', [])

        if not folders:
            bot.reply_to(message, "📂 در حال حاضر هیچ پوشه درسی در سیستم یافت نشد.")
            return

        markup = telebot.types.InlineKeyboardMarkup()
        buttons = [telebot.types.InlineKeyboardButton(text=f"📁 {f['name']}", callback_data=f"show_{f['id']}") for f in folders]

        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])

        bot.reply_to(message, "📚 **لیست دروس موجود:**\nبرای مشاهده فایل‌ها و PDFهای هر درس، دکمه آن را انتخاب کنید:", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"❌ خطا در ارتباط با گوگل درایو: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_'))
def callback_user_show_folder(call):
    folder_id = call.data.replace('show_', '')
    try:
        folder_meta = run_drive(lambda service: service.files().get(fileId=folder_id, fields="name").execute())
        course_name = folder_meta.get('name', 'نامشخص')

        results = run_drive(lambda service: service.files().list(
            q=f"'{folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'",
            fields="files(id, name, webViewLink)"
        ).execute())
        files = results.get('files', [])

        if not files:
            text = f"📂 **درس {course_name}:**\n❌ در حال حاضر هیچ فایل یا جزوه‌ای در این پوشه قرار نگرفته است."
        else:
            text = f"📂 **جزوات و منابع درس {course_name}:**\n\n"
            for idx, f in enumerate(files, 1):
                text += f"{idx}. 📄 [{f['name']}]({f['webViewLink']})\n"

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطا در خواندن اطلاعات: {str(e)}")

# ================== تگ‌های About و Help ==================
@bot.message_handler(commands=['about'])
def send_about(message):
    about_text = (
        "👤 **درباره سازنده:**\n"
        "این ربات توسط **AmirHKD** جهت تسهیل دسترسی دانشجویان به منابع درسی طراحی و توسعه یافته است.\n\n"
        "⚙️ **نحوه کارکرد فنی:**\n"
        "ربات به صورت مستقیم به فضاهای ذخیره‌سازی ابری گوگل‌درایو متصل است. هر زمان که فایل جدیدی در درایو آپدیت شود، ربات به صورت لحظه‌ای و پویا جدیدترین تغییرات را بدون نیاز به هارد سرور به شما نمایش می‌دهد."
    )
    bot.reply_to(message, about_text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "❓ **راهنمای استفاده از ربات:**\n\n"
        "1️⃣ ابتدا دستور `/files` را ارسال کنید تا لیست دروس برای شما لود شود.\n"
        "2️⃣ از روی کیبورد شیشه‌ای ظاهر شده، روی نام درس مورد نظر خود کلیک کنید.\n"
        "3️⃣ ربات لیست جزوات موجود را به همراه **لینک دانلود مستقیم و پرسرعت گوگل** به شما نمایش می‌دهد.\n\n"
        "📌 *نکته:* تمام لینک‌ها قابلیت دانلود مستقیم با برنامه‌های مدیریت دانلود را دارا هستند."
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "سلام! به ربات جزوات خوش آمدید 🎓✨\n\n"
        "📥 مشاهده پوشه درس‌ها: /files\n"
        "ℹ️ درباره ربات و سازنده: /about\n"
        "❓ راهنمای استفاده: /help"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.type == "private":
        bot.reply_to(message, f"❓ متوجه نشدم! برای دیدن پوشه‌های درسی از دستور `/files` استفاده کنید.")

# ================== وب‌هوک و سرور ==================
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    return 'ok', 403

@app.route('/')
def index():
    return "Bot is running successfully! 🚀", 200

if __name__ == "__main__":
    app.run()