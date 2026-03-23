import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask

app = Flask(__name__)

# --- तुमची माहिती इथे भरा ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MzY1MTg4LCJpYXQiOjE3NzQyNzg3ODgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.MYos_aoKx0Asovh4abb8mf-uiD7mNfY_-bVaq1YWNvJRpYrI_UBhJhZreE4TZ5uFgBZ_EmYLJ7avrDRbBeztAA" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# MCX Crude Oil आणि Natural Gas Security IDs
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Error sending telegram: {e}")

def scanner():
    # सिस्टीम सुरू झाल्यावर लगेच एक मेसेज पाठवेल
    send_telegram("🚀 *MCX ट्रेडिंग बॉट यशस्वीरित्या सुरू झाला आहे!* \nCrude Oil व Natural Gas स्कॅन होत आहे...")
    
    while True:
        now = datetime.now()
        # सकाळी ९ ते रात्री ११:३० (MCX वेळ)
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            for name, s_id in COMMODITIES.items():
                try:
                    # इंट्राडे डेटा मिळवणे
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            # साधी 'Sell' स्ट्रेटेजी: मागील कॅंडलचा लो ब्रेक झाला तर
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['low']:
                                    msg = f"🎯 *MCX SELL SIGNAL:* {name}\n💰 किंमत: {curr['close']}\n⏰ वेळ: {now.strftime('%H:%M:%S')}"
                                    send_telegram(msg)
                except Exception as e:
                    print(f"Scanner error: {e}")
                time.sleep(1)
        time.sleep(30)

@app.route('/')
def home():
    return "<h1>MCX Scanner is Live!</h1><p>Monitoring Crude Oil & Natural Gas.</p>", 200

if __name__ == "__main__":
    # Render साठी पोर्ट कॉन्फिगरेशन
    port = int(os.environ.get("PORT", 10000))
    # बॅकग्राउंडमध्ये स्कॅनर सुरू करणे
    Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
