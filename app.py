import os
import requests
import time
from datetime import datetime
from flask import Flask
from dhanhq import dhanhq
from threading import Thread

app = Flask(__name__)

# --- तुमची माहिती ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MjcxOTQ3LCJpYXQiOjE3NzQxODU1NDcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.kVtUEVvjiwCp9vG5oSYT4VJNN1anucqZJH17Z2AjxG1mCoFYrHlmNxffnaTdWMcGRsJWnPtOI-WT5Z5lqPQ7sw" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# प्रमुख १८० स्टॉक्सचे नमुने (यादी पूर्ण ठेवा)
STOCKS = {'RELIANCE': 2885, 'SBIN': 3045, 'HDFCBANK': 1333, 'ICICIBANK': 4963, 'TATAMOTORS': 3456}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except:
        print("Telegram Send Failed")

def scanner_loop():
    # १. सुरुवातीलाच एक मेसेज पाठवून खात्री करणे
    send_telegram("🔄 *स्कॅनर सिस्टीम रीफ्रेश झाली आहे!* \nआता 'Green -> Red' सेटअप शोधत आहे...")
    
    while True:
        try:
            now = datetime.now()
            # मार्केट वेळ: ९:१५ ते ३:३०
            if now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30):
                for name, s_id in STOCKS.items():
                    resp = dhan.historical_minute_charts(s_id, 'NSE_EQ', 'INTRA')
                    
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if data and len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            
                            # तुमची शुद्ध अट: Green -> Red Breakdown
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['low']:
                                    msg = f"🎯 *SELL:* {name}\nPrice: {curr['close']}\nTime: {now.strftime('%H:%M')}"
                                    send_telegram(msg)
                    
                    time.sleep(0.4) # API Rate Limit वाचवण्यासाठी
            else:
                print("Market is Closed")
                time.sleep(60)
        except Exception as e:
            # जर काही एरर आला तर तो टेलिग्रामवर कळेल
            send_telegram(f"⚠️ *System Alert:* {str(e)}")
            time.sleep(10)
        time.sleep(30)

@app.route('/')
def home():
    return "Scanner is LIVE and Running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=scanner_loop).start()
    app.run(host='0.0.0.0', port=port)
