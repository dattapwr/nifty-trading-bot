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

# सेक्टर्स आणि टॉप १० स्टॉक्स
SECTORS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS', 'ASHOKLEY.NS', 'TVSMOTOR.NS', 'BALKRISIND.NS', 'BHARATFORG.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'INDUSINDBK.NS', 'BANKBARODA.NS', 'FEDERALBNK.NS', 'IDFCFIRSTB.NS', 'AUBANK.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'LTIM.NS', 'TECHM.NS', 'PERSISTENT.NS', 'COFORGE.NS', 'MPHASIS.NS', 'LTTS.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'MANKIND.NS', 'TORNTPHARM.NS', 'LUPIN.NS', 'AUROPHARMA.NS', 'ZYDUSLIFE.NS', 'IPCALAB.NS'],
    '^CNXMETAL': ['TATASTEEL.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'SAIL.NS', 'NMDC.NS', 'NATIONALUM.NS', 'APLAPOLLO.NS', 'RATNAMANI.NS'],
    '^CNXFMCG': ['ITC.NS', 'HINDUNILVR.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'VBL.NS', 'GODREJCP.NS', 'TATACONSUM.NS', 'DABUR.NS', 'COLPAL.NS', 'MARICO.NS'],
    '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'ULTRACEMCO.NS', 'GRASIM.NS', 'NTPC.NS', 'POWERGRID.NS', 'ONGC.NS', 'BHARTIARTL.NS', 'DLF.NS'],
    '^CNXENERGY': ['RELIANCE.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'BPCL.NS', 'IOC.NS', 'GAIL.NS', 'ADANIGREEN.NS', 'ADANITRANS.NS', 'TATAPOWER.NS']
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: 
        requests.get(url, params=params, timeout=10)
    except: 
        pass

def get_top_sectors():
    performance = []
    for s_code in SECTORS.keys():
        try:
            d = yf.download(s_code, period='1d', interval='15m', progress=False, threads=False)
            if not d.empty:
                change = ((d['Close'].iloc[-1] - d['Open'].iloc[0]) / d['Open'].iloc[0]) * 100
                performance.append({'code': s_code.replace('^CNX', ''), 'change': float(change), 'full_code': s_code})
        except: continue
    
    if not performance: return [], []
    performance.sort(key=lambda x: x['change'], reverse=True)
    return performance[:2], performance[-2:]

def check_strategy(ticker, side):
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False, threads=False)
        if len(df) < 3: return None
        
        c0, c1, c2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
        # Inside Candle Logic
        is_inside = (float(c1['High']) < float(c2['High'])) and (float(c1['Low']) > float(c2['Low']))
        tm = datetime.now(IST).strftime('%H:%M:%S')
        
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

    # ९:१५ ते ३:३० वेळेत स्कॅनिंग
    if time(9, 15) <= now_ist.time() <= time(15, 30):
        market_open = True
        h2, l2 = get_top_sectors()
        
        # BUY Signals
        for s in h2:
            for t in SECTORS[s['full_code']]:
                res = check_strategy(t, "BUY")
                if res:
                    found_stocks.append(res)
                    # LAST_ALERTS काढल्यामुळे प्रत्येक रिफ्रेशला मेसेज जाईल
                    send_telegram(f"🚀 *BUY:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}\n⏰ Time: {res['t']}")
        
        # SELL Signals
        for s in l2:
            for t in SECTORS[s['full_code']]:
                res = check_strategy(t, "SELL")
                if res:
                    found_stocks.append(res)
                    send_telegram(f"📉 *SELL:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}\n⏰ Time: {res['t']}")

    return render_template('index.html', stocks=found_stocks, h2=h2, l2=l2, market_open=market_open,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
