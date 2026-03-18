import os
import pytz
import requests
from datetime import datetime, time
from flask import Flask, render_template
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzczOTAxNzcwLCJpYXQiOjE3NzM4MTUzNzAsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.IxHMt3yaFEGdmNmD0OoJRQ4LI0_74gicUNJMxRgMQP7ca7qrEokD5KZ9ssWfZUtKMhOcfKWZ7_G7cZH_QdkacA"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# Telegram Details
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []

# जास्तीत जास्त सिग्नल मिळण्यासाठी टॉप ५ ॲक्टिव्ह स्टॉक्स
WATCHLIST = [
    {'symbol': 'RELIANCE', 'sid': '2885'},
    {'symbol': 'HDFCBANK', 'sid': '1333'},
    {'symbol': 'SBIN', 'sid': '3045'},
    {'symbol': 'ICICIBANK', 'sid': '4963'},
    {'symbol': 'INFY', 'sid': '1594'}
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_strategy(stock):
    try:
        # १ मिनिटाचा डेटा मिळवणे
        data = dhan.get_intraday_data(
            security_id=stock['sid'],
            exchange_segment='NSE_EQ',
            instrument_type='EQUITY',
            interval=1, 
            from_date=datetime.now(IST).strftime('%Y-%m-%d'),
            to_date=datetime.now(IST).strftime('%Y-%m-%d')
        )

        if data.get('status') == 'success' and 'data' in data:
            d = data['data']
            if len(d['open']) < 5: return None

            # मागील पूर्ण झालेली कॅंडल (Index -3)
            prev_o, prev_h, prev_l, prev_c = float(d['open'][-3]), float(d['high'][-3]), float(d['low'][-3]), float(d['close'][-3])
            
            # नुकतीच संपलेली ताजी कॅंडल (Index -2)
            curr_o, curr_h, curr_l, curr_c = float(d['open'][-2]), float(d['high'][-2]), float(d['low'][-2]), float(d['close'][-2])
            
            candle_id = d['start_Time'][-2]
            display_time = datetime.now(IST).strftime('%H:%M:%S')

            # --- BREAKOUT STRATEGY ---
            
            # BUY: मागील कॅंडल Red होती आणि चालू कॅंडलने तिच्या HIGH च्या वर क्लोज दिले.
            if prev_c < prev_o and curr_c > prev_h:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'BUY'}

            # SELL: मागील कॅंडल Green होती आणि चालू कॅंडलने तिच्या LOW च्या खाली क्लोज दिले.
            if prev_c > prev_o and curr_c < prev_l:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'SELL'}
                
    except Exception as e:
        print(f"Error checking {stock['symbol']}: {e}")
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    # मार्केट वेळ: ९:१५ ते ३:३०
    market_active = time(9, 15) <= curr_time <= time(15, 30)
    
    found_stocks = []
    if market_active:
        for stock in WATCHLIST:
            res = check_strategy(stock)
            if res:
                # रिपिट सिग्नल टाळण्यासाठी चेक
                if not any(x['s'] == res['s'] and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                    SIGNAL_HISTORY.append(res)
                    icon = "🚀" if res['type'] == "BUY" else "📉"
                    send_telegram(f"{icon} *{res['type']} ALERT* \n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")
                    found_stocks.append(res)

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
