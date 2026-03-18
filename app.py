import os
import pytz
import requests
from datetime import datetime, time
from flask import Flask, render_template
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स (दिलेल्या टोकननुसार) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzczOTAxNzcwLCJpYXQiOjE3NzM4MTUzNzAsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.IxHMt3yaFEGdmNmD0OoJRQ4LI0_74gicUNJMxRgMQP7ca7qrEokD5KZ9ssWfZUtKMhOcfKWZ7_G7cZH_QdkacA"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# Telegram Details
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []

# महत्त्वाच्या स्टॉक्सची यादी (Security IDs सह - अचूकतेसाठी)
WATCHLIST = [
    {'symbol': 'RELIANCE', 'sid': '2885'},
    {'symbol': 'TCS', 'sid': '11536'},
    {'symbol': 'HDFCBANK', 'sid': '1333'},
    {'symbol': 'ICICIBANK', 'sid': '4963'},
    {'symbol': 'SBIN', 'sid': '3045'},
    {'symbol': 'INFY', 'sid': '1594'},
    {'symbol': 'TATAMOTORS', 'sid': '3456'},
    {'symbol': 'AXISBANK', 'sid': '5900'},
    {'symbol': 'WIPRO', 'sid': '3787'},
    {'symbol': 'BHARTIARTL', 'sid': '10604'}
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=5)
    except: pass

def check_strategy(stock):
    try:
        # धन कडून ५ मिनिटांचा डेटा मिळवणे
        data = dhan.get_intraday_data(
            security_id=stock['sid'],
            exchange_segment='NSE_EQ',
            instrument_type='EQUITY',
            interval='5', 
            from_date=datetime.now(IST).strftime('%Y-%m-%d'),
            to_date=datetime.now(IST).strftime('%Y-%m-%d')
        )

        if data.get('status') == 'success' and len(data['data']['open']) >= 3:
            # [-2] = मागील पूर्ण झालेली कॅंडल, [-3] = त्याच्या आधीची कॅंडल
            curr_o, curr_c = data['data']['open'][-2], data['data']['close'][-2]
            prev_o, prev_c = data['data']['open'][-3], data['data']['close'][-3]
            
            curr_green = curr_c > curr_o
            curr_red = curr_c < curr_o
            prev_green = prev_c > prev_o
            prev_red = prev_c < prev_o
            
            candle_id = data['data']['start_Time'][-2]
            display_time = datetime.now(IST).strftime('%H:%M:%S')

            # BUY: Red -> Green
            if prev_red and curr_green:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'BUY'}

            # SELL: Green -> Red
            if prev_green and curr_red:
                return {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'SELL'}
    except: pass
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
                found_stocks.append(res)
                # रिपिट सिग्नल टाळण्यासाठी चेक
                if not any(x['s'] == stock['symbol'] and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                    SIGNAL_HISTORY.append(res)
                    icon = "🚀" if res['type'] == "BUY" else "📉"
                    send_telegram(f"{icon} *{res['type']} (Dhan):* `{res['s']}` @ ₹{res['p']}\n⏰ वेळ: {res['t']}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
