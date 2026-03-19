import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9..." # तुमचा पूर्ण टोकन इथे टाका

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
LAST_CHECK_TIME = "Checking..."
CURRENT_LTP = {} # लेटेस्ट किंमत साठवण्यासाठी

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

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=10)
    except: pass

def check_strategy_loop():
    global LAST_CHECK_TIME
    send_telegram("✅ *Scanner Active with Heartbeat!*")
    
    heartbeat_counter = 0
    
    while True:
        try:
            now_ist = datetime.now(IST)
            LAST_CHECK_TIME = now_ist.strftime('%H:%M:%S')
            today = now_ist.strftime('%Y-%m-%d')
            
            # हार्टबीट मेसेज दर १५ मिनिटांनी (१५ लूप्स)
            heartbeat_counter += 1
            if heartbeat_counter >= 15:
                send_telegram(f"💓 *Heartbeat:* Bot is running fine. Time: {LAST_CHECK_TIME}")
                heartbeat_counter = 0

            for stock in WATCHLIST:
                data = None
                try:
                    data = dhan.intraday_minute_data(
                        security_id=stock['sid'], exchange_segment='NSE_EQ',
                        instrument_type='EQUITY', from_date=today, to_date=today
                    )
                except: continue

                if data and data.get('status') == 'success' and 'data' in data:
                    d = data['data']
                    if 'close' in d and len(d['close']) > 0:
                        # लेटेस्ट किंमत वेब पेजसाठी अपडेट करा
                        CURRENT_LTP[stock['symbol']] = d['close'][-1]
                        
                        if len(d['close']) >= 2:
                            prev_o = float(d['open'][-2])
                            prev_c = float(d['close'][-2])
                            curr_c = float(d['close'][-1])
                            candle_id = d['start_Time'][-1]
                            
                            # --- ट्रेडिंग लॉजिक ---
                            res = None
                            if prev_o > prev_c and curr_c > prev_o:
                                res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'BUY'}
                            elif prev_c > prev_o and curr_c < prev_o:
                                res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'SELL'}

                            if res and not any(x['s'] == res['s'] and x['id_t'] == candle_id for x in SIGNAL_HISTORY):
                                res['t'] = now_ist.strftime('%H:%M:%S')
                                res['id_t'] = candle_id
                                SIGNAL_HISTORY.append(res)
                                icon = "🟢" if res['type'] == "BUY" else "🔴"
                                send_telegram(f"{icon} *{res['type']} ALERT*\nStock: `{res['s']}`\nPrice: ₹{res['p']}")

                pytime.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")
        pytime.sleep(60)

threading.Thread(target=check_strategy_loop, daemon=True).start()

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
            .card { background: white; padding: 20px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 90%; max-width: 500px; }
            .ltp-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 15px; }
            .ltp-item { background: #e8f0fe; padding: 5px 10px; border-radius: 5px; font-size: 12px; border: 1px solid #c2d7fa; }
            .buy { color: green; font-weight: bold; } .sell { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Market Scanner <span style="color:#2ecc71;">● LIVE</span></h2>
            <p><b>Last Update:</b> {{ last_time }}</p>
            <p><b>Data Status:</b> {% if ltp %} ✅ Receiving Data {% else %} ❌ Waiting... {% endif %}</p>
            <hr>
            <h4>Live Prices (LTP):</h4>
            <div class="ltp-grid">
                {% for symbol, price in ltp.items() %}
                    <div class="ltp-item"><b>{{ symbol }}:</b> {{ price }}</div>
                {% endfor %}
            </div>
            <hr>
            <h4>Signal History:</h4>
            {% for s in history[:10] %}
                <p class="{{ s.type.lower() }}">[{{ s.t }}] {{ s.s }} - {{ s.type }} @ {{ s.p }}</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, last_time=LAST_CHECK_TIME, ltp=CURRENT_LTP, history=SIGNAL_HISTORY[::-1])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
