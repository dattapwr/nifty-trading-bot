import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask

app = Flask(__name__)

# १. तुमची माहिती भरा
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "तुमचा_नवीन_टोकन_इथे_टाका" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# २. आजचे ताजे आयडी
COMMODITIES = {
    'CRUDEOIL': 25145, 
    'NATURALGAS': 25147
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def commodity_scanner():
    send_telegram("🚀 *MCX बॉट आता लाईव्ह झाला आहे!* \nआजचे आयडी: CRUDE-25145, NG-25147")
    
    while True:
        now = datetime.now()
        # रात्री ११:३० पर्यंत स्कॅनिंग सुरू राहील
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            for name, s_id in COMMODITIES.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            # अट: Green -> Red Breakdown
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['low']:
                                    msg = f"🎯 *MCX SELL SIGNAL*\n\n*Stock:* {name}\n*Price:* {curr['close']}\n*Time:* {now.strftime('%H:%M')}"
                                    send_telegram(msg)
                except: continue
                time.sleep(1)
        time.sleep(30)

@app.route('/')
def health(): return "Scanner is Active!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=commodity_scanner).start()
    app.run(host='0.0.0.0', port=port)
