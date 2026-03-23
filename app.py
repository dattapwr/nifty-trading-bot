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
    'INFY': 1594, 'IOC': 1624, 'IRCTC': 13611, 'ITC': 1660, 'JINDALSTEL': 1722,
    'JSWSTEEL': 11723, 'JUBLFOOD': 18096, 'KOTAKBANK': 1922, 'L&TFH': 249, 'LICHSGFIN': 1997,
    'LT': 11483, 'LTIM': 17818, 'M&M': 2031, 'M&MFIN': 13285, 'MARUTI': 10999,
    'METROPOLIS': 9581, 'MFSL': 2142, 'MGL': 17534, 'MPHASIS': 4503, 'MRF': 2277,
    'MUTHOOTFIN': 23650, 'NATIONALUM': 6364, 'NAVINFLUOR': 14614, 'NESTLEIND': 17963, 'NMDC': 15332,
    'NTPC': 11630, 'ONGC': 2475, 'PAGEIND': 14413, 'PEL': 2662, 'PERSISTENT': 18365,
    'PETRONET': 11351, 'PFC': 14299, 'PIDILITIND': 2664, 'PNB': 10666, 'POLYCAB': 9590,
    'POWERGRID': 14977, 'PVRINOX': 13147, 'RELIANCE': 2885, 'SAIL': 2963, 'SBICARD': 17967,
    'SBILIFE': 21808, 'SBIN': 3045, 'SHREECEM': 3103, 'SIEMENS': 3150, 'SRF': 3247,
    'SUNPHARMA': 3351, 'SUNTV': 13404, 'SYNGENE': 10243, 'TATACHEM': 3405, 'TATACOMM': 3426,
    'TATACONSUM': 3432, 'TATAMOTORS': 3456, 'TATAPOWER': 3440, 'TATASTEEL': 3499, 'TCS': 11536,
    'TECHM': 13538, 'TITAN': 3506, 'TORNTPHARM': 3540, 'TRENT': 1964, 'TVSMOTOR': 3709,
    'UBL': 16713, 'ULTRACEMCO': 11532, 'UPL': 11287, 'VEDL': 3063, 'VOLTAS': 3718,
    'WIPRO': 3787, 'ZEEL': 3812, 'RECLTD': 15355, 'HAL': 2303, 'IRFC': 160, 'RVNL': 20,
    'DIXON': 21690, 'OBEROIRLTY': 20249, 'MAXHEALTH': 438, 'ABB': 15, 'TATAELXSI': 4451,
    'MCX': 31181, 'OFSS': 10738, 'COFORGE': 11543, 'HINDPETRO': 1406, 'PETRONET': 11351,
    'LUPIN': 1969, 'DIVISLAB': 7929, 'ALKEM': 11703, 'IPCALAB': 1633, 'BIOCON': 11373
    # ... (असे १८० पूर्ण स्टॉक्स या डिक्शनरीमध्ये आहेत)
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}&parse_mode=Markdown"
    try: requests.get(url, timeout=5)
    except: pass

def is_prev_day_red(s_id):
    """कालची डेली कॅन्डल लाल होती का तपासते"""
    try:
        now = datetime.now()
        start = (now - timedelta(days=5)).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        resp = dhan.historical_daily_charts(s_id, 'NSE_EQ', 'EQUITY', start, end)
        if resp['status'] == 'success':
            d = resp['data']
            # कालचा Close < कालचा Open = RED
            return d['close'][-2] < d['open'][-2]
    except: return False

def scanner_loop():
    global latest_signal, signal_count
    print("🚀 १८०+ स्टॉक्सचा 'Green-Red Breakdown' स्कॅनर सुरू झाला...")
    
    while True:
        now = datetime.now()
        # अट: मार्केट वेळ ९:३० ते १५:३०
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

                        prev = data[-2] # सेटअप कॅन्डल (९:३० नंतरची कोणतीही ग्रीन)
                        curr = data[-1] # सिग्नल कॅन्डल (जिने लो तोडला)

                        # २. अट: मागील कॅन्डल हिरवी (Green)
                        # ३. अट: चालू कॅन्डल लाल (Red)
                        # ४. अट: चालू कॅन्डलने मागील हिरवीचा Low तोडला पाहिजे
                        if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                            if curr['close'] < prev['low']:
                                entry = curr['close']
                                # ५. ०.१५% बफर स्टॉपलॉस
                                sl = round(prev['high'] * 1.0015, 2)
                                # ६. १:२ टार्गेट
                                risk = sl - entry
                                tgt = round(entry - (risk * 2), 2)
                                
                                msg = (f"🎯 *SELL SIGNAL (Trend Breakdown)*\n\n"
                                       f"*Stock:* {name}\n*Entry:* {entry}\n"
                                       f"*SL (0.15% Buffer):* {sl}\n*TGT (1:2):* {tgt}\n"
                                       f"*Time:* {now.strftime('%H:%M')}")
                                
                                send_telegram(msg)
                                signal_count[name] = signal_count.get(name, 0) + 1
                                latest_signal = {"stock": name, "price": entry, "side": "SELL", "time": now.strftime('%H:%M')}

                    time.sleep(0.3) # API दर मर्यादेसाठी
                except: continue
        time.sleep(60)

@app.route('/')
def index():
    return render_template('index.html', **latest_signal)

if __name__ == "__main__":
    Thread(target=scanner_loop).start()
    app.run(host='0.0.0.0', port=10000)
