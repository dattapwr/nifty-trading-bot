import os
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from flask import Flask, render_template
from dhanhq import dhanhq
from threading import Thread

app = Flask(__name__)

# --- कॉन्फिगरेशन ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "तुमचा_टोकन_इथे_टाका" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
latest_signal = {"stock": "SCANNING", "price": "Waiting", "time": "Live"}
sent_signals = []

# १८०+ स्टॉक्सची लिस्ट (वेळेअभावी काही महत्त्वाचे दिले आहेत, तुम्ही अधिक जोडू शकता)
STOCKS = {
    'RELIANCE': '2885', 'SBIN': '3045', 'TCS': '11536', 'INFY': '1594', 'HDFCBANK': '1333',
    'ICICIBANK': '4963', 'AXISBANK': '5900', 'TATAMOTORS': '3456', 'TATASTEEL': '3499'
    # ... बाकीचे आयडी वरून कॉपी करून येथे पेस्ट करा
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}&parse_mode=Markdown"
    try: requests.get(url, timeout=5)
    except: pass

def get_data(s_id):
    # Dhan API नुसार सुधारित फंक्शन
    return dhan.historical_minute_charts(int(s_id), 'NSE_EQ', 'INTRA')

def scanner_loop():
    global latest_signal, sent_signals
    while True:
        now = datetime.now()
        # मार्केट वेळेतच स्कॅन करा (9:15 ते 3:30)
        if now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30):
            for name, s_id in STOCKS.items():
                if name in sent_signals: continue
                
                try:
                    resp = get_data(s_id)
                    if resp and 'data' in resp:
                        df = pd.DataFrame(resp['data'])
                        if len(df) < 5: continue

                        prev = df.iloc[-2]
                        curr = df.iloc[-1]

                        # लॉजिक: Body Breakdown (Green Low च्या खाली Red Close)
                        if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                            if curr['close'] < prev['low']:
                                entry = curr['close']
                                msg = f"🎯 *SELL SIGNAL!* \n\n*Stock:* {name}\n*Entry:* {entry}\n*Time:* {now.strftime('%H:%M')}"
                                send_telegram(msg)
                                sent_signals.append(name)
                                latest_signal = {"stock": name, "price": entry, "time": now.strftime('%H:%M')}
                    
                    time.sleep(0.5) # API Rate Limit टाळण्यासाठी
                except Exception as e:
                    print(f"Error scanning {name}: {e}")
            
            time.sleep(60) # प्रत्येक १ मिनिटाला पुन्हा चेक करा
        else:
            time.sleep(300)

@app.route('/')
def index():
    return render_template('index.html', stock=latest_signal['stock'], price=latest_signal['price'], time=latest_signal['time'])

if __name__ == "__main__":
    # स्कॅनर वेगळ्या थ्रेडमध्ये सुरू करा
    Thread(target=scanner_loop).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
