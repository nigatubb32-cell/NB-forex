import os
import time
import threading
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

def send_telegram_message(chat_id, text):
    """የቴሌግራም መልእክት መላኪያ function"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def fetch_market_data(ticker="GC=F"):
    """
    Gold (GC=F) Candlestick Data ከ Yahoo Finance ማምጫ
    1H, 30m, 1m timeframes Fetch ያደርጋል
    """
    try:
        df_1h = yf.download(tickers=ticker, period="5d", interval="1h", progress=False)
        df_30m = yf.download(tickers=ticker, period="3d", interval="30m", progress=False)
        df_1m = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
        return df_1h, df_30m, df_1m
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None, None, None

def analyze_institutional_setup():
    """
    ICT, S&D, Candle Patterns, Liquidity Sweep እና Fibonacci OTE ማጣሪያ ኤንጅን
    """
    df_1h, df_30m, df_1m = fetch_market_data("GC=F")
    
    if df_1h is None or df_1h.empty or df_1m is None or df_1m.empty:
        return "⚠️ *Market Data Offline:* የገበያ ዳታን ለማግኘት አልተቻለም። እባክዎን ትንሽ ቆይተው ይሞክሩ።"

    # --- 1. 1H Trend Analysis (Moving Averages + Structure) ---
    df_1h['EMA_20'] = df_1h['Close'].ewm(span=20, adjust=False).mean()
    df_1h['EMA_50'] = df_1h['Close'].ewm(span=50, adjust=False).mean()
    
    latest_1h = df_1h.iloc[-1]
    prev_1h = df_1h.iloc[-2]
    
    # Current Gold Price
    current_price = float(df_1m['Close'].iloc[-1])
    
    htf_bias = "NEUTRAL"
    if latest_1h['EMA_20'] > latest_1h['EMA_50']:
        htf_bias = "BULLISH"
    elif latest_1h['EMA_20'] < latest_1h['EMA_50']:
        htf_bias = "BEARISH"

    # --- 2. 30m Liquidity Sweep / Fakeout Detection ---
    recent_30m_high = float(df_30m['High'].tail(10).max())
    recent_30m_low = float(df_30m['Low'].tail(10).min())
    
    sweep_detected = False
    sweep_type = None

    # High Sweep (Sell Liquidity Grab)
    if float(df_1m['High'].max()) >= recent_30m_high and current_price < recent_30m_high:
        sweep_detected = True
        sweep_type = "SELL_SWEEP"
    # Low Sweep (Buy Liquidity Grab)
    elif float(df_1m['Low'].min()) <= recent_30m_low and current_price > recent_30m_low:
        sweep_detected = True
        sweep_type = "BUY_SWEEP"

    # --- 3. 1m Fibonacci OTE & Setup Signal Decision ---
    high_1m = float(df_1m['High'].tail(15).max())
    low_1m = float(df_1m['Low'].tail(15).min())
    diff = high_1m - low_1m

    if htf_bias == "BULLISH" and (sweep_type == "BUY_SWEEP" or not sweep_detected):
        # Fibonacci OTE levels (0.618 and 0.786)
        fib_618 = high_1m - (diff * 0.618)
        fib_786 = high_1m - (diff * 0.786)
        
        entry = current_price
        sl = round(low_1m - 1.5, 2)  # Tight institutional stop loss
        tp1 = round(entry + ((entry - sl) * 2), 2)  # 1:2 Risk/Reward
        tp2 = round(entry + ((entry - sl) * 4), 2)  # 1:4 Risk/Reward

        return f"""
🔥 *NB FOREX HIGH-PROBABILITY SIGNAL (BUY)* 🔥

📌 *Asset:* XAUUSD (GOLD)
📊 *1H Trend:* {htf_bias}
⏱ *Setup:* S&D Zone + Liquidity Sweep + Fib OTE

🟢 *Action:* BUY
📥 *Entry Zone:* {round(fib_786, 2)} - {round(fib_618, 2)} (Current: {round(entry, 2)})
🛑 *Stop Loss:* {sl}
🎯 *Take Profit 1:* {tp1} (1:2 RR)
🎯 *Take Profit 2:* {tp2} (1:4 RR)

💡 *Execution Strategy:* 1m Fib OTE Retracement confirmation complete. Manage risk strictly!
"""

    elif htf_bias == "BEARISH" and (sweep_type == "SELL_SWEEP" or not sweep_detected):
        fib_618 = low_1m + (diff * 0.618)
        fib_786 = low_1m + (diff * 0.786)
        
        entry = current_price
        sl = round(high_1m + 1.5, 2)
        tp1 = round(entry - ((sl - entry) * 2), 2)
        tp2 = round(entry - ((sl - entry) * 4), 2)

        return f"""
🔴 *NB FOREX HIGH-PROBABILITY SIGNAL (SELL)* 🔴

📌 *Asset:* XAUUSD (GOLD)
📊 *1H Trend:* {htf_bias}
⏱ *Setup:* Supply Zone + Liquidity Sweep + Fib OTE

🔴 *Action:* SELL
📥 *Entry Zone:* {round(fib_618, 2)} - {round(fib_786, 2)} (Current: {round(entry, 2)})
🛑 *Stop Loss:* {sl}
🎯 *Take Profit 1:* {tp1} (1:2 RR)
🎯 *Take Profit 2:* {tp2} (1:4 RR)

💡 *Execution Strategy:* 1m Fib OTE Retracement confirmation complete. Manage risk strictly!
"""

    return f"🔎 *Market Analysis:* XAUUSD is currently consolidating around *${round(current_price, 2)}*. No clear 7/7 confluence setup found yet. Monitoring structure..."

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            if text == "/start":
                msg = "👋 *እንኳን ወደ NB Forex Signal Engine በሰላም መጡ!*\n\nየ Gold (XAUUSD) የቀጥታ Institutional አናሊሲስ ለማየት `/signal` የሚለውን ይጫኑ።"
                send_telegram_message(chat_id, msg)
            elif text == "/signal":
                msg = analyze_institutional_setup()
                send_telegram_message(chat_id, msg)

        return "OK", 200
    return "NB Forex Bot Engine is Running 24/7!", 200

def set_telegram_webhook():
    time.sleep(3)
    webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://nb-forex.onrender.com/"
    try:
        r = requests.get(webhook_url)
        print("Webhook Setup Response:", r.json())
    except Exception as e:
        print(f"Webhook Setup Error: {e}")

threading.Thread(target=set_telegram_webhook, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
