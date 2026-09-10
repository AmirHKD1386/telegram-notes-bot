import os
import telebot
from flask import Flask
import threading

# دریافت توکن ربات از متغیرهای محیطی (برای امنیت بیشتر)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# --- کدهای ربات تلگرام ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "سلام! من یک ربات هستم که روی سرور رندر به صورت ۲۴ ساعته فعال شده‌ام.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"شما گفتید: {message.text}")

# --- کدهای وب‌سرور Flask برای بیدار نگه داشتن ربات ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

# تابعی برای اجرای ربات تلگرام
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # اجرای ربات تلگرام در یک Thread (رشته) جداگانه تا با Flask تداخل نداشته باشد
    threading.Thread(target=run_bot).start()
    
    # اجرای وب‌سرور Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
