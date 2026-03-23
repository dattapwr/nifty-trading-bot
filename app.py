import os
import requests
import time
from datetime import datetime
from flask import Flask
from dhanhq import dhanhq
from threading import Thread

app = Flask(__name__)

# --- तुमची माहिती (मी अपडेट केली आहे) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MjcxOTQ3LCJpYXQiOjE3NzQxODU1NDcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.kVtUEVvjiwCp9vG5oSYT4VJNN1anucqZJH17Z2AjxG1mCoFYrHlmNxffnaTdWMcGRsJWnPtOI-WT5Z5lqPQ7sw" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# १८० स्टॉक्सची यादी
STOCKS = {'ACC': 22, 'ADANIENT': 25, 'RELIANCE': 2885, 'SBIN': 3045, 'TCS': 11536} # इ.

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def scanner_loop():
    # हा मेसेज तुमच्या फोनवर आलाच पाहिजे!
    send_telegram("✅ *तुमचा ट्रेडिंग बॉट आता पूर्णपणे कनेक्ट झाला आहे!* \nआता ९:१५ ते ३:३० सिग्नल येतील.")
    
    while True:
        now = datetime.now()
        if now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30):
            for name, s_id in STOCKS.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'NSE_EQ', 'INTRA')
                    if resp and resp['status'] == 'success':
                        data = resp['data']
                        prev, curr = data[-2], data[-1]
                        
                        # तुमची अट: Green -> Red Breakdown
                        if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                            if curr['close'] < prev['low']:
                                msg = f"🎯 *SELL SIGNAL:* {name}\nPrice: {curr['close']}"
                                send_telegram(msg)
                    time.sleep(0.5)
                except: continue
        time.sleep(30)

@app.route('/')
def health():
    return "Bot is Active!", 200

if __name__ == "__main__":
    # Render साठी पोर्ट सेटिंग
    port = int(os.environ.get("PORT", 10000))
    Thread(target=scanner_loop).start()
    app.run(host='0.0.0.0', port=port)
