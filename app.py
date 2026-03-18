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

# Watchlist: Crude Oil आणि Natural Gas (MCX)
WATCHLIST = [
    {'symbol': 'CRUDEOIL', 'sid': '25'}, 
    {'symbol': 'NATURALGAS', 'sid': '31'}
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=5)
    except:
        pass

def check_strategy(stock):
    try:
        data = dhan.get_intraday_data(
            security_id=stock['sid'],
            exchange_segment='MCX_FO',
            instrument_type='FUTCOM',
            interval=1, 
            from_date=datetime.now(IST).strftime('%Y-%m-%d'),
            to_date=datetime.now(IST).strftime('%Y-%m-%d')
        )

        if data.get('status') == 'success' and 'data' in data:
            d = data['data']
            if len(d['open']) < 3: return None

            # [-3] = मागील कॅंडल, [-2] = नुकतीच क्लोज झालेली कॅंडल
            prev_o, prev_c = float(d['open'][-3]), float(d['close'][-3])
            curr_o, curr_c = float(d['open'][-2]), float(d['close'][-2])
            
            candle_id = d['start_Time'][-2]
            display_time = datetime.now(IST).strftime('%H:%M:%S')

            # --- ONLY BODY LOGIC (Wicks ignored) ---
            
            # BUY: मागील कॅंडल Red होती (Close < Open) 
            # आणि चालू कॅंडलचा Close मागील कॅंडलच्या Open (High Body) च्या वर आहे.
            if prev_c < prev_o and curr_c > prev_o:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'BUY'}

            # SELL: मागील कॅंडल Green होती (Close > Open) 
            # आणि चालू कॅंडलचा Close मागील कॅंडलच्या Open (Low Body) च्या खाली आहे.
            if prev_c > prev_o and curr_c < prev_o:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'SELL'}
                
    except Exception as e:
        print(f"Error checking {stock['symbol']}: {e}")
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    
    # मार्केट वेळ (MCX साठी सकाळी ९ ते रात्री ११:३०)
    market_active = time(9, 0) <= curr_time <= time(23, 30)
    
    found_stocks = []
    if market_active:
        for stock in WATCHLIST:
            res = check_strategy(stock)
            if res:
                # एकाच कॅंडलवर वारंवार सिग्नल येऊ नये म्हणून चेक
                if not any(x['s'] == res['s'] and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                    SIGNAL_HISTORY.append(res)
                    icon = "🛢️" if "CRUDE" in res['s'] else "🔥"
                    trend = "🚀 BUY" if res['type'] == "BUY" else "📉 SELL"
                    send_telegram(f"{icon} *{trend} SIGNAL*\n\nStock: `{res['s']}`\nPrice: {res['p']}\nTime: {res['t']}\n(Body Breakout)")
                    found_stocks.append(res)

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
