import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask

app = Flask(__name__)

# --- तुमची माहिती भरा ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MzY1MTg4LCJpYXQiOjE3NzQyNzg3ODgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.MYos_aoKx0Asovh4abb8mf-uiD7mNfY_-bVaq1YWNvJRpYrI_UBhJhZreE4TZ5uFgBZ_EmYLJ7avrDRbBeztAA" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# MCX चालू महिन्याचे Security IDs
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def scanner():
    send_telegram("🚀 *MCX बॉट सुरू झाला आहे!* \nफक्त Crude Oil व Natural Gas स्कॅन होत आहे.")
    while True:
        now = datetime.now()
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            for name, s_id in COMMODITIES.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['low']:
                                    msg = f"🎯 *MCX SELL:* {name}\nकिंमत: {curr['close']}\nवेळ: {now.strftime('%H:%M')}"
                                    send_telegram(msg)
                except: continue
                time.sleep(1)
        time.sleep(30)

@app.route('/')
def home(): return "Scanner LIVE", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=scanner).start()
    app.run(host='0.0.0.0', port=port)
