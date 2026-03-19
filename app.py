import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स (नवीन टोकन वापरा) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "YOUR_NEW_TOKEN_HERE" # <--- तुमचा नवीन टोकन इथे टाका

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
LAST_CHECK_TIME = "Waiting..."

# --- Reliance स्टॉक डिटेल्स ---
# Reliance चा SID '2885' आहे आणि सेगमेंट 'NSE_EQ' आहे
WATCHLIST = [
    {'symbol': 'RELIANCE', 'sid': '2885'}
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: 
        requests.get(url, params=params, timeout=10)
    except: 
        pass

def check_strategy_loop():
    global LAST_CHECK_TIME
    send_telegram("🚀 *Bot Started for RELIANCE!* \nMonitoring NSE Market...")
    
    while True:
        try:
            now_ist = datetime.now(IST)
            LAST_CHECK_TIME = now_ist.strftime('%H:%M:%S')
            today = now_ist.strftime('%Y-%m-%d')
            
            # मार्केट वेळेनुसार (९:१५ ते ३:३०)
            for stock in WATCHLIST:
                data = None
                for _ in range(3): # Retry logic
                    try:
                        data = dhan.intraday_minute_data(
                            security_id=stock['sid'],
                            exchange_segment='NSE_EQ', # Reliance साठी NSE_EQ वापरले
                            instrument_type='EQUITY',
                            from_date=today,
                            to_date=today
                        )
                        if data.get('status') == 'success': break
                    except:
                        pytime.sleep(2)

                if data and data.get('status') == 'success' and 'data' in data:
                    d = data['data']
                    if 'open' in d and len(d['open']) >= 2:
                        prev_o = float(d['open'][-2])
                        prev_c = float(d['close'][-2])
                        curr_o = float(d['open'][-1])
                        curr_c = float(d['close'][-1])
                        candle_id = d['start_Time'][-1]
                        
                        res = None
                        # --- मुख्य ट्रेडिंग लॉजिक (Body to Body Breakout) ---
                        # BUY: आदली कॅंडल लाल आणि चालू क्लोजिंग आदल्या ओपनच्या वर
                        if prev_o > prev_c and curr_c > prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'BUY'}
                        
                        # SELL: आदली कॅंडल हिरवी आणि चालू क्लोजिंग आदल्या ओपनच्या खाली
                        elif prev_c > prev_o and curr_c < prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'SELL'}

                        if res:
                            # डुप्लिकेट सिग्नल टाळण्यासाठी चेक
                            if not any(x['s'] == res['s'] and x['id_t'] == candle_id for x in SIGNAL_HISTORY):
                                res['t'] = now_ist.strftime('%H:%M:%S')
                                res['id_t'] = candle_id
                                SIGNAL_HISTORY.append(res)
                                icon = "🟢" if res['type'] == "BUY" else "🔴"
                                send_telegram(f"{icon} *{res['type']} ALERT*\n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")

        except Exception as e:
            print(f"Error: {e}")
        
        pytime.sleep(60) # दर १ मिनिटाला चेक करा

# Background Thread
threading.Thread(target=check_strategy_loop, daemon=True).start()

@app.route('/')
def home():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="30">
        <title>Reliance Trading Bot</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding-top: 50px; background: #eceff1; }
            .card { background: white; padding: 30px; border-radius: 15px; display: inline-block; box-shadow: 0 10px 20px rgba(0,0,0,0.1); border-top: 5px solid #007bff; }
            .buy { color: #2ecc71; font-weight: bold; }
            .sell { color: #e74c3c; font-weight: bold; }
            .status { color: #2980b9; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Reliance Bot Status: <span style="color:#2ecc71;">LIVE</span></h1>
            <p class="status"><b>Last Scan:</b> {{ last_time }}</p>
            <p><b>Signals:</b> {{ count }}</p>
            <hr>
            <h3>Signal Log:</h3>
            {% if history %}
                {% for s in history %}
                    <p class="{{ s.type.lower() }}">[{{ s.t }}] {{ s.s }} - {{ s.type }} @ {{ s.p }}</p>
                {% endfor %}
            {% else %}
                <p style="color:#7f8c8d;">कंडिशन मॅच होण्याची वाट पाहत आहे...</p>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, last_time=LAST_CHECK_TIME, count=len(SIGNAL_HISTORY), history=SIGNAL_HISTORY[::-1])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
