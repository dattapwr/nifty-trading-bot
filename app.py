import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask, render_template_string

app = Flask(__name__)

# --- तुमची माहिती ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "EyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MzY1MTg4LCJpYXQiOjE3NzQyNzg3ODgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.MYos_aoKx0Asovh4abb8mf-uiD7mNfY_-bVaq1YWNvJRpYrI_UBhJhZreE4TZ5uFgBZ_EmYLJ7avrDRbBeztAA"
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
# लेटेस्ट Security IDs तपासा (उदा. CRUDEOIL APR FUT)
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

latest_signals_list = []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def scanner():
    global latest_signals_list
    send_telegram("🚀 *MCX बॉट आता ५ मिनिटांच्या टाइमफ्रेमवर सुरू झाला आहे!*")
    
    while True:
        now = datetime.now()
        # मार्केट वेळ (MCX): सकाळी ९:०० ते रात्री ११:३०
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            for name, s_id in COMMODITIES.items():
                try:
                    # '5' म्हणजे ५ मिनिटांचा चार्ट
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '5') 
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if len(data) >= 2:
                            prev = data[-2]  # मागील ५ मिनिटांची कॅंडल
                            curr = data[-1]  # चालू ५ मिनिटांची कॅंडल
                            
                            # १. पहिली कॅंडल हिरवी (Close > Open)
                            is_prev_green = prev['close'] > prev['open']
                            # २. दुसरी कॅंडल लाल (Close < Open)
                            is_curr_red = curr['close'] < curr['open']
                            
                            # ३. Body-to-Body Sell अट: लाल क्लोज < हिरवा ओपन
                            if is_prev_green and is_curr_red:
                                if curr['close'] < prev['open']:
                                    sig_msg = f"🎯 *5-MIN SELL:* {name} \n💰 किंमत: {curr['close']} \n⏰ वेळ: {now.strftime('%H:%M:%S')}"
                                    if sig_msg not in latest_signals_list:
                                        latest_signals_list.insert(0, sig_msg)
                                        latest_signals_list = latest_signals_list[:10]
                                        send_telegram(sig_msg)
                except: continue
                time.sleep(2)
        time.sleep(60) # दर मिनिटाला एकदा चेक करेल

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MCX 5-Min Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: sans-serif; background-color: #0d1117; color: white; text-align: center; padding: 20px; }
        .dashboard { max-width: 500px; margin: auto; background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; }
        .signal-box { background: #d9534f; color: white; padding: 10px; margin: 10px 0; border-radius: 6px; font-weight: bold; text-align: left; }
        .header { color: #f0ad4e; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h2 class="header">📊 MCX 5-Min Dashboard</h2>
        <p style="color: #3fb950;">● Status: Live & Scanning (5M)</p>
        <hr style="border: 0.1px solid #30363d;">
        {% if signals %}
            {% for s in signals %}
                <div class="signal-box">{{ s }}</div>
            {% endfor %}
        {% else %}
            <p>५ मिनिटांच्या ब्रेकआउटची वाट पाहत आहे...</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE, signals=latest_signals_list)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
