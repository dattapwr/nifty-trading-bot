import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask, render_template_string

app = Flask(__name__)

# --- तुमची माहिती (मी आधीच भरली आहे) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "EyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MzY1MTg4LCJpYXQiOjE3NzQyNzg3ODgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.MYos_aoKx0Asovh4abb8mf-uiD7mNfY_-bVaq1YWNvJRpYrI_UBhJhZreE4TZ5uFgBZ_EmYLJ7avrDRbBeztAA"
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

# वेबसाईटवर दाखवण्यासाठी ग्लोबल व्हेरिएबल
latest_signal = "सध्या कोणताही सिग्नल नाही. स्कॅनिंग सुरू आहे..."
last_update_time = "-"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def scanner():
    global latest_signal, last_update_time
    send_telegram("🚀 *MCX बॉट सुरू झाला!* \nवेबसाईट आणि टेलिग्राम दोन्हीवर सिग्नल मिळतील.")
    
    while True:
        now = datetime.now()
        # मार्केट वेळ: सकाळी ९ ते रात्री ११:३०
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            for name, s_id in COMMODITIES.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            # Sell स्ट्रेटेजी
                            if prev['close'] > prev['open'] and curr['close'] < curr['open'] and curr['close'] < prev['low']:
                                last_update_time = now.strftime('%H:%M:%S')
                                latest_signal = f"🎯 SELL: {name} | किंमत: {curr['close']} | वेळ: {last_update_time}"
                                send_telegram(latest_signal)
                except: continue
                time.sleep(2)
        time.sleep(30)

# वेबसाईटचे डिझाइन (HTML)
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MCX Live Scanner</title>
    <meta http-equiv="refresh" content="30"> <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; padding: 50px; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0,0,0,0.1); display: inline-block; }
        .signal { font-size: 24px; color: #d9534f; font-weight: bold; margin: 20px 0; }
        .status { color: #5cb85c; font-weight: bold; }
        .footer { margin-top: 20px; font-size: 12px; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 MCX Live Signal Dashboard</h1>
        <p class="status">● System Live & Scanning</p>
        <hr>
        <div class="signal">{{ signal }}</div>
        <p>शेवटचा अपडेट: {{ update_time }}</p>
        <div class="footer">Client ID: 1105760761 | Crude Oil & Natural Gas</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE, signal=latest_signal, update_time=last_update_time)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
