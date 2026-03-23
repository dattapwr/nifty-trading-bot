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

# १८०+ NSE स्टॉक्सची यादी
STOCKS = {
    'ACC': 22, 'ADANIENT': 25, 'ADANIPORTS': 15083, 'AMBUJACEM': 1270, 'ASHOKLEY': 212,
    'ASIANPAINT': 236, 'AXISBANK': 5900, 'BAJAJ-AUTO': 16669, 'BAJFINANCE': 317, 
    'BANKBARODA': 4668, 'BHARTIARTL': 10604, 'HDFCBANK': 1333, 'ICICIBANK': 4963, 
    'INFY': 1594, 'ITC': 1660, 'RELIANCE': 2885, 'SBIN': 3045, 'TCS': 11536
    # (तुमच्या १८० स्टॉक्सची पूर्ण यादी इथे ठेवा)
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}&parse_mode=Markdown"
    try: requests.get(url, timeout=5)
    except: pass

def get_prev_close(s_id):
    try:
        now = datetime.now()
        start = (now - timedelta(days=5)).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        resp = dhan.historical_daily_charts(s_id, 'NSE_EQ', 'EQUITY', start, end)
        return resp['data']['close'][-2] if resp['status'] == 'success' else None
    except: return None

def scanner_loop():
    global latest_signal
    # बॉट सुरू झाल्यावर लगेच एक टेस्ट मेसेज
    send_telegram("🚀 *स्कॅनर सुरू झाला आहे!* \nआता आदल्या दिवशीचा फिल्टर काढला आहे. मेसेज येण्याची वाट पाहत आहे...")
    
    while True:
        now = datetime.now()
        # सकाळी ९:३० नंतर स्कॅनिंग सुरू
        if now.weekday() < 5 and (9, 30) <= (now.hour, now.minute) <= (15, 30):
            for name, s_id in STOCKS.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'NSE_EQ', 'INTRA')
                    if resp and resp['status'] == 'success':
                        data = resp['data']
                        if len(data) < 2: continue

                        p_close = get_prev_close(s_id)
                        if not p_close: continue
                        
                        # गॅप फिल्टर: २% (मेसेज लवकर येण्यासाठी ५% वरून २% केला आहे)
                        gap_pct = abs((data[0]['open'] - p_close) / p_close) * 100
                        if gap_pct < 2.0: continue 

                        prev = data[-2] # सेटअप: कोणतीही ग्रीन कॅन्डल
                        curr = data[-1] # सिग्नल: रेड कॅन्डल जिने लो तोडला

                        # अट: ग्रीन कॅन्डलचा लो रेड कॅन्डलने तोडला पाहिजे
                        if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                            if curr['close'] < prev['low']:
                                entry = curr['close']
                                sl = round(prev['high'] * 1.0015, 2) # ०.१५% बफर
                                risk = sl - entry
                                tgt = round(entry - (risk * 2), 2)
                                
                                msg = (f"🎯 *NEW SELL SIGNAL*\n"
                                       f"*Stock:* {name}\n"
                                       f"*Gap:* {round(gap_pct, 2)}%\n"
                                       f"*Entry:* {entry}\n"
                                       f"*SL:* {sl}\n"
                                       f"*TGT:* {tgt}\n"
                                       f"*Time:* {now.strftime('%H:%M')}")
                                
                                send_telegram(msg)
                                latest_signal = {"stock": name, "price": entry, "side": "SELL", "time": now.strftime('%H:%M')}
                                time.sleep(1) # एकाच वेळी अनेक मेसेज टाळण्यासाठी
                                
                    time.sleep(0.3) # API दर मर्यादेसाठी
                except: continue
        time.sleep(30) # दर ३० सेकंदाला पुन्हा तपासणे

@app.route('/')
def index():
    return render_template('index.html', **latest_signal)

if __name__ == "__main__":
    Thread(target=scanner_loop).start()
    app.run(host='0.0.0.0', port=10000)
