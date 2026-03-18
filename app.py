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

# लोड कमी करण्यासाठी फक्त ५ महत्त्वाचे स्टॉक्स (Heavyweight Stocks)
WATCHLIST = [
    {'symbol': 'RELIANCE', 'sid': '2885'},
    {'symbol': 'HDFCBANK', 'sid': '1333'},
    {'symbol': 'ICICIBANK', 'sid': '4963'},
    {'symbol': 'SBIN', 'sid': '3045'},
    {'symbol': 'INFY', 'sid': '1594'}
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=2) # Timeout कमी केला आहे
    except: pass

def check_strategy(stock):
    try:
        # intraday_data - interval ५ मिनिटे (Integer)
        data = dhan.get_intraday_data(
            security_id=stock['sid'],
            exchange_segment='NSE_EQ',
            instrument_type='EQUITY',
            interval=5, 
            from_date=datetime.now(IST).strftime('%Y-%m-%d'),
            to_date=datetime.now(IST).strftime('%Y-%m-%d')
        )

        if data.get('status') == 'success' and 'data' in data:
            d = data['data']
            if len(d['open']) < 3: return None

            # [-2] = मागील पूर्ण झालेली कॅंडल, [-3] = त्याच्या आधीची
            curr_o, curr_c = float(d['open'][-2]), float(d['close'][-2])
            prev_o, prev_c = float(d['open'][-3]), float(d['close'][-3])
            
            candle_id = d['start_Time'][-2]
            display_time = datetime.now(IST).strftime('%H:%M:%S')

            # BUY: मागील Red (prev_c < prev_o) + चालू Green (curr_c > curr_o)
            if prev_c < prev_o and curr_c > curr_o:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'BUY'}

            # SELL: मागील Green (prev_c > prev_o) + चालू Red (curr_c < curr_o)
            if prev_c > prev_o and curr_c < curr_o:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'SELL'}
    except: pass
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    market_active = time(9, 15) <= curr_time <= time(15, 30)
    
    found_stocks = []
    if market_active:
        for stock in WATCHLIST:
            res = check_strategy(stock)
            if res:
                found_stocks.append(res)
                # रिपिट रोखण्यासाठी: स्टॉक नाव + प्रकार + कॅंडलची वेळ तिन्ही तपासले जातात
                if not any(x['s'] == res['s'] and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                    SIGNAL_HISTORY.append(res)
                    icon = "🚀" if res['type'] == "BUY" else "📉"
                    send_telegram(f"{icon} *{res['type']} (Dhan):* `{res['s']}` @ ₹{res['p']}\n⏰ वेळ: {res['t']}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    # Render साठी पोर्ट सेटिंग
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
