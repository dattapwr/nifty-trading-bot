import os
import requests
import time
from datetime import datetime, timedelta
from flask import Flask, render_template
from dhanhq import dhanhq
from threading import Thread

app = Flask(__name__)

# --- तुमची माहिती ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MjcxOTQ3LCJpYXQiOjE3NzQxODU1NDcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.kVtUEVvjiwCp9vG5oSYT4VJNN1anucqZJH17Z2AjxG1mCoFYrHlmNxffnaTdWMcGRsJWnPtOI-WT5Z5lqPQ7sw" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
latest_signal = {"stock": "SCANNING", "price": "Waiting", "side": "NONE", "time": "Live"}

# १८०+ NSE स्टॉक्सची यादी (Security IDs)
STOCKS = {
    'ACC': 22, 'ADANIENT': 25, 'ADANIPORTS': 15083, 'AMBUJACEM': 1270, 'ASHOKLEY': 212,
    'ASIANPAINT': 236, 'AXISBANK': 5900, 'BAJAJ-AUTO': 16669, 'BAJFINANCE': 317, 
    'BANKBARODA': 4668, 'BHARTIARTL': 10604, 'HDFCBANK': 1333, 'ICICIBANK': 4963, 
    'INFY': 1594, 'ITC': 1660, 'RELIANCE': 2885, 'SBIN': 3045, 'TCS': 11536,
    'TATAMOTORS': 3456, 'WIPRO': 3787, 'JSWSTEEL': 11723, 'LT': 11483, 'PNB': 10666,
    'VEDL': 3063, 'DLF': 14732, 'CANBK': 10791, 'TATASTEEL': 3499, 'BPCL': 526
    # (इतर १८० स्टॉक्सची यादी मागे दिली आहे तशीच जोडा)
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}&parse_mode=Markdown"
    try: 
        requests.get(url, timeout=5)
    except: pass

def scanner_loop():
    global latest_signal
    # सर्व्हिस सुरू झाल्याचा पहिला मेसेज (टेस्टिंगसाठी)
    send_telegram("🚀 *अल्गो स्कॅनर आता पूर्णपणे सुरू झाला आहे!* \n९:३० आणि गॅप या सर्व अटी काढल्या आहेत. \nआता ९:१५ पासून मेसेज येतील.")
    
    while True:
        now = datetime.now()
        # सोमवार ते शुक्रवार, ९:१५ ते ३:३० (मार्केटची संपूर्ण वेळ)
        if now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30):
            for name, s_id in STOCKS.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'NSE_EQ', 'INTRA')
                    if resp and resp['status'] == 'success':
                        data = resp['data']
                        if len(data) < 2: continue

                        # मागील ५ मिनिटांची कॅन्डल (Setup) आणि चालू कॅन्डल (Signal)
                        prev = data[-2]
                        curr = data[-1]

                        # अट: १. मागील हिरवी (Green) २. चालू लाल (Red) ३. लाल ने हिरवीचा 'Low' तोडला
                        if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                            if curr['close'] < prev['low']:
                                entry = curr['close']
                                sl = round(prev['high'] * 1.0015, 2) # ०.१५% बफर SL
                                tgt = round(entry - ((sl - entry) * 2), 2) # १:२ Target
                                
                                msg = (f"🎯 *SELL SIGNAL (No Restrictions)*\n\n"
                                       f"*Stock:* {name}\n"
                                       f"*Entry:* {entry}\n"
                                       f"*SL:* {sl}\n"
                                       f"*TGT:* {tgt}\n"
                                       f"*Time:* {now.strftime('%H:%M:%S')}")
                                
                                send_telegram(msg)
                                latest_signal = {"stock": name, "price": entry, "side": "SELL", "time": now.strftime('%H:%M')}
                                
                    time.sleep(0.2) # १८० स्टॉक्स वेगाने स्कॅन करण्यासाठी
                except: continue
        time.sleep(30)

@app.route('/')
def index():
    return render_template('index.html', **latest_signal)

if __name__ == "__main__":
    Thread(target=scanner_loop).start()
    app.run(host='0.0.0.0', port=10000)
