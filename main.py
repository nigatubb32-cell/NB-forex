import os
import time
import threading
import requests
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Web Service Render ላይ መስራቱን ለማረጋገጥ የሚያገለግል Flask App
app = Flask(__name__)

@app.route('/')
def home():
    return "NB Forex Bot Engine is Running 24/7!"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

def trading_bot_loop():
    print("Forex Signal Engine Started...")
    send_telegram_message("🚀 *NB Forex Signal Bot (Web Service) Activated!*")
    
    while True:
        try:
            # የገበያ አናሊሲስ እዚህ ጋር ይሄዳል
            # print("Analyzing XAUUSD...")
            time.sleep(60)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(10)

# ቦቱን በ Background Thread ለማስነሳት
bot_thread = threading.Thread(target=trading_bot_loop, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
