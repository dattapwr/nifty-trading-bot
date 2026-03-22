import os
import pandas as pd
import requests
import time
from datetime import datetime
from flask import Flask, render_template
from dhanhq import dhanhq
from threading import Thread

app = Flask(__name__)

# --- तुमची माहिती भरा ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MjcxOTQ3LCJpYXQiOjE3NzQxODU1NDcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.kVtUEVvjiwCp9vG5oSYT4VJNN1anucqZJH17Z2AjxG1mCoFYrHlmNxffnaTdWMcGRsJWnPtOI-WT5Z5lqPQ7sw" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
latest_signal = {"stock": "SCANNING", "price": "Waiting", "side": "NONE", "time": "Live"}
sent_signals = []

# १८०+ प्रमुख F&O स्टॉक्स (नमुना यादी - तुम्ही अधिक जोडू शकता)
STOCKS = {
    'RELIANCE': 2885, 'SBIN': 3045, 'TCS': 11536, 'INFY': 1594, 'HDFCBANK': 1333,
    'ICICIBANK': 4963, 'AXISBANK': 5900, 'TATAMOTORS': 3456, 'TATASTEEL': 3499,
    'BHARTIARTL': 10604, 'ADANIENT': 25, 'BAJFINANCE': 317, 'LT': 11483, 'ITC': 1660
    # ... उर्वरित स्टॉक्सचे आयडी असेच जोडा
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}&parse_mode=Markdown"
    try: requests.get(url, timeout=5)
    except: pass

def scanner_loop():
    global latest_signal, sent_signals
    while True:
        now = datetime.now()
        if now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30):
            for name, s_id in STOCKS.items():
                if f"{name}_{now.strftime('%H:%M')}" in sent_signals: continue
                
                try:
                    resp = dhan.historical_minute_charts(s_id, 'NSE_EQ', 'INTRA')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if len(data) >= 2:
                            prev, curr = data[-2], data[-1]

                            # 🚀 BUY LOGIC (GREEN)
                            if prev['close'] < prev['open'] and curr['close'] > curr['open']:
                                if curr['close'] > prev['high']:
                                    msg = f"🚀 *BUY SIGNAL!* \n\n*Stock:* {name}\n*Price:* {curr['close']}\n*Time:* {now.strftime('%H:%M')}"
                                    send_telegram(msg)
                                    sent_signals.append(f"{name}_{now.strftime('%H:%M')}")
                                    latest_signal = {"stock": name, "price": curr['close'], "side": "BUY", "time": now.strftime('%H:%M')}

                            # 🎯 SELL LOGIC (RED)
                            elif prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['low']:
                                    msg = f"🎯 *SELL SIGNAL!* \n\n*Stock:* {name}\n*Price:* {curr['close']}\n*Time:* {now.strftime('%H:%M')}"
                                    send_telegram(msg)
                                    sent_signals.append(f"{name}_{now.strftime('%H:%M')}")
                                    latest_signal = {"stock": name, "price": curr['close'], "side": "SELL", "time": now.strftime('%H:%M')}
                    
                    time.sleep(0.3) 
                except: continue
            time.sleep(60)
        else:
            time.sleep(300)

@app.route('/')
def index():
    # 'side' नुसार डॅशबोर्डवर रंग बदलण्यासाठी हे डेटा पाठवते
    return render_template('index.html', **latest_signal)

if __name__ == "__main__":
    Thread(target=scanner_loop).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
