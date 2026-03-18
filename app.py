import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
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

# --- १८ मार्च २०२६ साठी MCX IDs ---
WATCHLIST = [
    {'symbol': 'CRUDEOIL MAR FUT', 'sid': '64115'}, 
    {'symbol': 'NATURALGAS MAR FUT', 'sid': '64132'}
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=5)
    except: pass

def check_strategy():
    while True: # सतत चालण्यासाठी लूप
        now_ist = datetime.now(IST)
        print(f"--- Checking Market at {now_ist.strftime('%H:%M:%S')} ---")
        
        for stock in WATCHLIST:
            try:
                data = dhan.get_intraday_data(
                    security_id=stock['sid'],
                    exchange_segment='MCX_FO',
                    instrument_type='FUTCOM',
                    interval=1, 
                    from_date=now_ist.strftime('%Y-%m-%d'),
                    to_date=now_ist.strftime('%Y-%m-%d')
                )

                if data.get('status') == 'success' and 'data' in data:
                    d = data['data']
                    if len(d['open']) >= 2:
                        # [-2] मागील पूर्ण कॅंडल | [-1] चालू भाव (LTP)
                        prev_o, prev_c = float(d['open'][-2]), float(d['close'][-2])
                        curr_c = float(d['close'][-1])
                        candle_id = d['start_Time'][-1]
                        
                        # --- तुमच्या चित्राप्रमाणे बॉडी लॉजिक ---
                        res = None
                        # BUY: मागील रेड कॅंडलच्या Open च्या वर सध्याची किंमत गेली तर
                        if prev_o > prev_c and curr_c > prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 't': now_ist.strftime('%H:%M:%S'), 'id_t': candle_id, 'type': 'BUY'}
                        
                        # SELL: मागील ग्रीन कॅंडलच्या Open च्या खाली सध्याची किंमत गेली तर
                        elif prev_c > prev_o and curr_c < prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 't': now_ist.strftime('%H:%M:%S'), 'id_t': candle_id, 'type': 'SELL'}

                        if res:
                            # डुप्लिकेट टाळण्यासाठी चेक
                            if not any(x['s'] == res['s'] and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                                SIGNAL_HISTORY.append(res)
                                icon = "🚀" if res['type'] == "BUY" else "📉"
                                send_telegram(f"{icon} *{res['type']} ALERT*\n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")
                                print(f"SENT TO TELEGRAM: {res['s']} {res['type']}")

            except Exception as e:
                print(f"Error checking {stock['symbol']}: {e}")
        
        pytime.sleep(60) # १ मिनिट थांबा आणि पुन्हा चेक करा

# --- बॅकग्राउंड थ्रेड सुरू करा ---
threading.Thread(target=check_strategy, daemon=True).start()

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    return render_template('index.html', history=SIGNAL_HISTORY[::-1], 
                           market_open=True, 
                           date=now_ist.strftime('%d-%m-%Y'), 
                           time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
