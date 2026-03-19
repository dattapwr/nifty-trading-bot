import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स (खात्री करा की हा टोकन नवीन आहे) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "इथे_तुमचा_पूर्ण_टोकन_टाका" 

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
LAST_CHECK_TIME = "Checking..."
DATA_ERROR = "None"
CURRENT_LTP = {}

WATCHLIST = [
    {'symbol': 'RELIANCE', 'sid': '2885'}, {'symbol': 'TCS', 'sid': '11536'},
    {'symbol': 'HDFCBANK', 'sid': '1333'}, {'symbol': 'ICICIBANK', 'sid': '4963'},
    {'symbol': 'INFY', 'sid': '1594'}, {'symbol': 'SBIN', 'sid': '3045'},
    {'symbol': 'BHARTIARTL', 'sid': '10604'}, {'symbol': 'LICI', 'sid': '11802'},
    {'symbol': 'ITC', 'sid': '1660'}, {'symbol': 'HINDUNILVR', 'sid': '1394'},
    {'symbol': 'LT', 'sid': '11483'}, {'symbol': 'BAJFINANCE', 'sid': '317'},
    {'symbol': 'KOTAKBANK', 'sid': '1922'}, {'symbol': 'ADANIENT', 'sid': '25'},
    {'symbol': 'AXISBANK', 'sid': '5900'}, {'symbol': 'ASIANPAINT', 'sid': '236'},
    {'symbol': 'MARUTI', 'sid': '10999'}, {'symbol': 'SUNPHARMA', 'sid': '3351'},
    {'symbol': 'TITAN', 'sid': '3506'}, {'symbol': 'TATASTEEL', 'sid': '3499'}
]

def scan_markets():
    global LAST_CHECK_TIME, DATA_ERROR
    now_ist = datetime.now(IST)
    LAST_CHECK_TIME = now_ist.strftime('%H:%M:%S')
    today = now_ist.strftime('%Y-%m-%d')
    
    for stock in WATCHLIST:
        try:
            data = dhan.intraday_minute_data(
                security_id=stock['sid'], exchange_segment='NSE_EQ',
                instrument_type='EQUITY', from_date=today, to_date=today
            )
            if data and data.get('status') == 'success':
                DATA_ERROR = "Connected ✅"
                d = data.get('data', {})
                if d and 'close' in d and len(d['close']) > 0:
                    cc = d['close'][-1]
                    CURRENT_LTP[stock['symbol']] = cc
                    
                    # बॉडी-टू-बॉडी लॉजिक
                    if len(d['close']) >= 2:
                        po, pc = d['open'][-2], d['close'][-2]
                        cid = d['start_Time'][-1]
                        
                        res = None
                        if po > pc and cc > po: res = 'BUY'
                        elif pc > po and cc < po: res = 'SELL'
                        
                        if res and not any(x['s'] == stock['symbol'] and x['id_t'] == cid for x in SIGNAL_HISTORY):
                            msg = f"{'🟢' if res=='BUY' else '🔴'} *{res} SIGNAL*\nStock: `{stock['symbol']}`\nPrice: ₹{cc}"
                            requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}&parse_mode=Markdown")
                            SIGNAL_HISTORY.append({'s': stock['symbol'], 'p': cc, 'type': res, 't': LAST_CHECK_TIME, 'id_t': cid})
            else:
                DATA_ERROR = f"API Error: {data.get('remarks', 'Unknown')}"
        except Exception as e:
            DATA_ERROR = f"System Error: {str(e)}"
        pytime.sleep(0.2)

def background_loop():
    while True:
        scan_markets()
        pytime.sleep(60)

threading.Thread(target=background_loop, daemon=True).start()

@app.route('/')
def home():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="30">
        <title>Stock Scanner</title>
        <style>
            body { font-family: sans-serif; text-align: center; background: #f4f7f6; padding: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; width: 100%; max-width: 500px; }
            .status { font-weight: bold; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; text-align: left; }
            .item { background: #eef2f7; padding: 8px; border-radius: 4px; font-size: 13px; }
            .buy { color: green; font-weight: bold; } .sell { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Market Scanner 🚀</h2>
            <div class="status" style="background: {% if '✅' in err %} #d4edda {% else %} #f8d7da {% endif %};">
                Status: {{ err }} | Time: {{ last_time }}
            </div>
            <div class="grid">
                {% for s, p in ltp.items() %}
                    <div class="item"><b>{{ s }}:</b> ₹{{ p }}</div>
                {% endfor %}
            </div>
            <hr>
            <h4>Signals Today:</h4>
            {% for s in history %}
                <p class="{{ s.type.lower() }}">[{{ s.t }}] {{ s.s }} - {{ s.type }} @ {{ s.p }}</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, last_time=LAST_CHECK_TIME, ltp=CURRENT_LTP, history=SIGNAL_HISTORY[::-1], err=DATA_ERROR)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
