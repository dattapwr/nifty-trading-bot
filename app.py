import os
import requests
import time
from datetime import datetime, timedelta
from flask import Flask, render_template
from dhanhq import dhanhq
from threading import Thread

app = Flask(__name__)

# --- Configuration ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MjcxOTQ3LCJpYXQiOjE3NzQxODU1NDcsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.kVtUEVvjiwCp9vG5oSYT4VJNN1anucqZJH17Z2AjxG1mCoFYrHlmNxffnaTdWMcGRsJWnPtOI-WT5Z5lqPQ7sw" 
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
latest_signal = {"stock": "SCANNING", "price": "Waiting", "side": "NONE", "time": "Live"}
signal_count = {}

# १८०+ NSE स्टॉक्सची यादी (Security IDs)
STOCKS = {
    'ACC': 22, 'ADANIENT': 25, 'ADANIPORTS': 15083, 'AMBUJACEM': 1270, 'ASHOKLEY': 212,
    'ASIANPAINT': 236, 'AUBANK': 21238, 'AUROPHARMA': 275, 'AXISBANK': 5900, 'BAJAJ-AUTO': 16669,
    'BAJFINANCE': 317, 'BAJAJFINSV': 16675, 'BALKRISIND': 335, 'BANDHANBNK': 2263, 'BANKBARODA': 4668,
    'BATAINDIA': 371, 'BEL': 383, 'BERGEPAINT': 404, 'BHARTIARTL': 10604, 'BHEL': 438,
    'BPCL': 526, 'BRITANNIA': 547, 'CANBK': 10791, 'CHOLAFIN': 685, 'CIPLA': 694,
    'COALINDIA': 20374, 'CONCOR': 4745, 'CUMMINSIND': 1901, 'DABUR': 772, 'DLF': 14732,
    'EICHERMOT': 910, 'ESCORTS': 951, 'EXIDEIND': 970, 'FEDERALBNK': 1023, 'GAIL': 4812,
    'GLENMARK': 7406, 'GMRINFRA': 13528, 'GODREJCP': 10099, 'GODREJPROP': 17875, 'GRASIM': 1232,
    'HAVELLS': 9819, 'HCLTECH': 7229, 'HDFCBANK': 1333, 'HDFCLIFE': 467, 'HEROMOTOCO': 1348,
    'HINDALCO': 1363, 'HINDCOPPER': 1373, 'HINDPETRO': 1406, 'HINDUNILVR': 1394, 'ICICIBANK': 4963,
    'ICICIGI': 21770, 'ICICIPRULI': 18652, 'IDFCFIRSTB': 11184, 'IEX': 220, 'IGL': 11262,
    'INDHOTEL': 1512, 'INDIACEM': 1515, 'INDIAMART': 10726, 'INDIGO': 11195, 'INDUSINDBK': 5258,
    'INFY': 1594, 'IOC': 1624, 'IRCTC': 13611, 'ITC': 1660, 'JSWSTEEL': 11723, 'RELIANCE': 2885, 'SBIN': 3045, 'TCS': 11536
    # ... (उर्वरित १८० स्टॉक्सचे आयडी असेच जोडा)
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

def is_prev_day_red(s_id):
    try:
        now = datetime.now()
        start = (now - timedelta(days=5)).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        resp = dhan.historical_daily_charts(s_id, 'NSE_EQ', 'EQUITY', start, end)
        if resp['status'] == 'success':
            d = resp['data']
            return d['close'][-2] < d['open'][-2]
    except: return False

def scanner_loop():
    global latest_signal, signal_count
    print("🚀 ५% गॅप + Green-Red Breakdown स्कॅनर सुरू झाला...")
    
    while True:
        now = datetime.now()
        if now.weekday() < 5 and (9, 30) <= (now.hour, now.minute) <= (15, 30):
            for name, s_id in STOCKS.items():
                if signal_count.get(name, 0) >= 2: continue
                
                try:
                    # १. काल लाल दिवस होता का?
                    if not is_prev_day_red(s_id): continue

                    resp = dhan.historical_minute_charts(s_id, 'NSE_EQ', 'INTRA')
                    if resp['status'] == 'success':
                        data = resp['data']
                        if len(data) < 2: continue

                        p_close = get_prev_close(s_id)
                        if not p_close: continue
                        
                        # २. ५% गॅप फिल्टर (गॅप ५% किंवा त्यापेक्षा जास्त हवा)
                        gap_pct = abs((data[0]['open'] - p_close) / p_close) * 100
                        if gap_pct < 5.0: continue 

                        prev = data[-2] # हिरवी कॅन्डल (९:३० नंतरची)
                        curr = data[-1] # लाल कॅन्डल (जिने लो तोडला)

                        # ३. तुमची मुख्य अट (Green -> Red Breakdown)
                        if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                            if curr['close'] < prev['low']:
                                entry = curr['close']
                                sl = round(prev['high'] * 1.0015, 2) # ०.१५% बफर
                                risk = sl - entry
                                tgt = round(entry - (risk * 2), 2) # १:२ टार्गेट
                                
                                msg = (f"🎯 *SELL SIGNAL (5% GAP FOUND)*\n\n"
                                       f"*Stock:* {name}\n*Gap:* {round(gap_pct, 2)}%\n"
                                       f"*Entry:* {entry}\n*SL:* {sl}\n*TGT:* {tgt}\n"
                                       f"*Time:* {now.strftime('%H:%M')}")
                                
                                send_telegram(msg)
                                signal_count[name] = signal_count.get(name, 0) + 1
                                latest_signal = {"stock": name, "price": entry, "side": "SELL", "time": now.strftime('%H:%M')}

                    time.sleep(0.3)
                except: continue
        time.sleep(60)

@app.route('/')
def index():
    return render_template('index.html', **latest_signal)

if __name__ == "__main__":
    Thread(target=scanner_loop).start()
    app.run(host='0.0.0.0', port=10000)
