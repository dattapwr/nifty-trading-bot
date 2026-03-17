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

# सेक्टर आणि त्यातील प्रमुख स्टॉक्स
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
    for s_code in SECTORS.keys():
        try:
            # १ दिवसाचा डेटा घेऊन बदल मोजणे
            d = yf.download(s_code, period='1d', interval='15m', progress=False)
            if not d.empty:
                change = ((d['Close'].iloc[-1] - d['Open'].iloc[0]) / d['Open'].iloc[0]) * 100
                performance.append({'code': s_code.replace('^CNX', ''), 'change': change, 'full_code': s_code})
        except: continue
    
    performance.sort(key=lambda x: x['change'], reverse=True)
    high_2 = performance[:2]
    low_2 = performance[-2:]
    return high_2, low_2

def check_strategy(ticker, side):
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False)
        if len(df) < 3: return None
        
        c0, c1, c2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
        # Inside Candle: c1 candle c2 च्या आत हवी
        is_inside = (c1['High'] < c2['High']) and (c1['Low'] > c2['Low'])
        
        tm = datetime.now(IST).strftime('%H:%M')
        
        if side == "BUY" and is_inside and (c0['Close'] > c1['High']):
            return {'s': ticker, 'p': round(c0['Close'], 2), 't': tm, 'type': 'BUY'}
        
        if side == "SELL" and is_inside and (c0['Close'] < c1['Low']):
            return {'s': ticker, 'p': round(c0['Close'], 2), 't': tm, 'type': 'SELL'}
    except: return None
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    found_stocks = []
    h2, l2 = [], []

    # मार्केट वेळ: ९:१५ ते ३:३०
    if time(9, 15) <= now_ist.time() <= time(15, 30):
        h2, l2 = get_top_sectors()
        
        # BUY: फक्त वाढणाऱ्या सेक्टर्समधील स्टॉक्स स्कॅन करणे
        for s in h2:
            for t in SECTORS[s['full_code']]:
                res = check_strategy(t, "BUY")
                if res: 
                    found_stocks.append(res)
                    if f"{t}_B" not in LAST_ALERTS:
                        send_telegram(f"🚀 *BUY ALERT:* `{t}`\n💰 Price: ₹{res['p']}\n📊 Sector: {s['code']}")
                        LAST_ALERTS[f"{t}_B"] = True

        # SELL: फक्त पडणाऱ्या सेक्टर्समधील स्टॉक्स स्कॅन करणे
        for s in l2:
            for t in SECTORS[s['full_code']]:
                res = check_strategy(t, "SELL")
                if res: 
                    found_stocks.append(res)
                    if f"{t}_S" not in LAST_ALERTS:
                        send_telegram(f"📉 *SELL ALERT:* `{t}`\n💰 Price: ₹{res['p']}\n📊 Sector: {s['code']}")
                        LAST_ALERTS[f"{t}_S"] = True

    return render_template('index.html', stocks=found_stocks, 
                           h2=h2, l2=l2,
                           date=now_ist.strftime('%d-%m-%Y'),
                           time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
