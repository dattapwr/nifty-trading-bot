import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

# Telegram Details
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []

# सर्व ८ सेक्टर्सचे स्टॉक्स
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
    try: requests.get(url, params=params, timeout=10)
    except: pass

def check_strategy(ticker):
    try:
        # ५ मिनिटांच्या इंटरव्हलवर डेटा मिळवणे
        df = yf.download(ticker, period='1d', interval='5m', progress=False, threads=True)
        if len(df) < 2: return None
        
        # c0 = सध्याची क्लोज झालेली कॅन्डल, c1 = मागील कॅन्डल
        c0, c1 = df.iloc[-1], df.iloc[-2]
        
        c0_green = float(c0['Close']) > float(c0['Open'])
        c0_red = float(c0['Close']) < float(c0['Open'])
        c1_green = float(c1['Close']) > float(c1['Open'])
        c1_red = float(c1['Close']) < float(c1['Open'])

        tm = datetime.now(IST).strftime('%H:%M:%S')

        # BUY अट: १ली लाल (c1) आणि त्यानंतर लगेच २री हिरवी (c0) क्लोज झाली
        if c1_red and c0_green:
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'BUY'}

        # SELL अट: १ली हिरवी (c1) आणि त्यानंतर लगेच २री लाल (c0) क्लोज झाली
        if c1_green and c0_red:
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'SELL'}
                
    except: return None
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    # सकाळी ९:१५ ते ३:३० दरम्यान स्कॅनिंग चालू राहील
    market_active = time(9, 15) <= curr_time <= time(15, 30)
    
    found_stocks = []

    if market_active:
        for sector, tickers in SECTORS.items():
            for t in tickers:
                res = check_strategy(t)
                if res:
                    found_stocks.append(res)
                    # जर हा सिग्नल आजच्या इतिहासात नसेल तरच मेसेज पाठवा
                    if not any(x['s'] == t and x['type'] == res['type'] and x['t'][:5] == res['t'][:5] for x in SIGNAL_HISTORY):
                        SIGNAL_HISTORY.append(res)
                        icon = "🚀" if res['type'] == "BUY" else "📉"
                        send_telegram(f"{icon} *{res['type']}:* `{t}` @ ₹{res['p']}\n📊 Sector: {sector}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
