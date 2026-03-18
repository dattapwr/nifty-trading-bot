import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time
from flask import Flask, render_template

app = Flask(__name__)

# Telegram Details
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []

# लोड कमी करण्यासाठी फक्त १० महत्त्वाचे स्टॉक्स
WATCHLIST = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'LT.NS', 'M&M.NS'
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=5)
    except: pass

def check_strategy(ticker):
    try:
        # ५ मिनिटांचा डेटा, वेगासाठी threads=False ठेवले आहे कारण स्टॉक कमी आहेत
        df = yf.download(ticker, period='1d', interval='5m', progress=False)
        if len(df) < 2: return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        curr_green = float(curr['Close']) > float(curr['Open'])
        curr_red = float(curr['Close']) < float(curr['Open'])
        prev_green = float(prev['Close']) > float(prev['Open'])
        prev_red = float(prev['Close']) < float(prev['Open'])
        
        # युनिक आयडीसाठी कॅन्डलची वेळ
        candle_id = df.index[-1].astimezone(IST).strftime('%H:%M')
        display_time = datetime.now(IST).strftime('%H:%M:%S')

        # BUY अट: १ली लाल + २री हिरवी क्लोज 
        if prev_red and curr_green:
            return {'s': ticker, 'p': round(float(curr['Close']), 2), 't': display_time, 'id_t': candle_id, 'type': 'BUY'}

        # SELL अट: १ली हिरवी + २री लाल क्लोज 
        if prev_green and curr_red:
            return {'s': ticker, 'p': round(float(curr['Close']), 2), 't': display_time, 'id_t': candle_id, 'type': 'SELL'}
    except: return None
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    # सकाळी ९:१५ ते ३:३० मार्केट चालू असतानाच स्कॅनिंग होईल
    market_active = time(9, 15) <= curr_time <= time(15, 30)
    
    found_stocks = []
    if market_active:
        for t in WATCHLIST:
            res = check_strategy(t)
            if res:
                found_stocks.append(res)
                # रिपीट सिग्नल रोखण्यासाठी अट
                if not any(x['s'] == t and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                    SIGNAL_HISTORY.append(res)
                    icon = "🚀" if res['type'] == "BUY" else "📉"
                    send_telegram(f"{icon} *{res['type']}:* `{t}` @ ₹{res['p']}\n⏰ वेळ: {res['t']}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
