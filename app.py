import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time
from flask import Flask, render_template

app = Flask(__name__)

# --- तुमची माहिती ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

LAST_ALERTS = {}

# सेक्टर्स आणि स्टॉक्स
SECTORS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'ASHOKLEY.NS', 'BAJAJ-AUTO.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'LUPIN.NS'],
    '^CNXMETAL': ['TATASTEEL.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS'],
    '^CNXFMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS'],
    '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'GRASIM.NS'],
    '^CNXENERGY': ['ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BPCL.NS']
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=5)
    except: pass

def get_top_sectors():
    performance = []
    for s_code, tickers in SECTORS.items():
        try:
            d = yf.download(s_code, period='1d', interval='15m', progress=False)
            if not d.empty:
                change = ((d['Close'].iloc[-1] - d['Open'].iloc[0]) / d['Open'].iloc[0]) * 100
                performance.append({'code': s_code.replace('^CNX', ''), 'change': float(change), 'full_code': s_code})
        except: continue
    
    if not performance: return [], []
    performance.sort(key=lambda x: x['change'], reverse=True)
    return performance[:2], performance[-2:]

def check_strategy(ticker, side):
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False)
        if len(df) < 3: return None
        
        c0, c1, c2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
        is_inside = (float(c1['High']) < float(c2['High'])) and (float(c1['Low']) > float(c2['Low']))
        tm = datetime.now(IST).strftime('%H:%M')
        
        if side == "BUY" and is_inside and (float(c0['Close']) > float(c1['High'])):
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'BUY'}
        if side == "SELL" and is_inside and (float(c0['Close']) < float(c1['Low'])):
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'SELL'}
    except: return None
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    found_stocks, h2, l2 = [], [], []
    market_open = False

    # वेळ ९:१५ ते ३:३० सेट केली आहे
    if time(9, 15) <= now_ist.time() <= time(15, 30):
        market_open = True
        h2, l2 = get_top_sectors()
        for s in h2:
            for t in SECTORS[s['full_code']]:
                res = check_strategy(t, "BUY")
                if res: 
                    found_stocks.append(res)
                    if f"{t}_B" not in LAST_ALERTS:
                        send_telegram(f"🚀 *BUY:* `{t}` @ ₹{res['p']}")
                        LAST_ALERTS[f"{t}_B"] = True
        for s in l2:
            for t in SECTORS[s['full_code']]:
                res = check_strategy(t, "SELL")
                if res: 
                    found_stocks.append(res)
                    if f"{t}_S" not in LAST_ALERTS:
                        send_telegram(f"📉 *SELL:* `{t}` @ ₹{res['p']}")
                        LAST_ALERTS[f"{t}_S"] = True

    return render_template('index.html', stocks=found_stocks, h2=h2, l2=l2, market_open=market_open,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
