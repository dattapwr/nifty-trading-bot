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
ACCESS_TOKEN = "YOUR_NEW_TOKEN_HERE" # तुमचा नवीन टोकन इथे टाका

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
LAST_CHECK_TIME = "Checking..."

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
    send_telegram("🚀 *Reliance Bot is now ACTIVE!* \nWatching for Body-to-Body signals...")
    
    while True:
        try:
            now_ist = datetime.now(IST)
            LAST_CHECK_TIME = now_ist.strftime('%H:%M:%S')
            today = now_ist.strftime('%Y-%m-%d')
            
            for stock in WATCHLIST:
                data = None
                try:
                    data = dhan.intraday_minute_data(
                        security_id=stock['sid'],
                        exchange_segment='NSE_EQ',
                        instrument_type='EQUITY',
                        from_date=today,
                        to_date=today
                    )
                except Exception as e:
                    print(f"API Error: {e}")

                if data and data.get('status') == 'success' and 'data' in data:
                    d = data['data']
                    if 'open' in d and len(d['open']) >= 2:
                        prev_o = float(d['open'][-2])
                        prev_c = float(d['close'][-2])
                        curr_c = float(d['close'][-1])
                        candle_id = d['start_Time'][-1]
                        
                        res = None
                        # --- खरे ट्रेडिंग लॉजिक ---
                        # BUY: आदली कॅंडल लाल आणि चालू क्लोजिंग आदल्या ओपनच्या वर
                        if prev_o > prev_c and curr_c > prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'BUY'}
                        
                        # SELL: आदली कॅंडल हिरवी आणि चालू क्लोजिंग आदल्या ओपनच्या खाली
                        elif prev_c > prev_o and curr_c < prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'SELL'}

                        if res:
                            # एकाच कॅंडलवर पुन्हा मेसेज नको म्हणून चेक
                            if not any(x['s'] == res['s'] and x['id_t'] == candle_id for x in SIGNAL_HISTORY):
                                res['t'] = now_ist.strftime('%H:%M:%S')
                                res['id_t'] = candle_id
                                SIGNAL_HISTORY.append(res)
                                icon = "🟢" if res['type'] == "BUY" else "🔴"
                                send_telegram(f"{icon} *{res['type']} SIGNAL*\n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")

        except Exception as e:
            print(f"Loop Error: {e}")
        
        pytime.sleep(60)

threading.Thread(target=check_strategy_loop, daemon=True).start()

@app.route('/')
def home():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="30">
        <title>Reliance Scanner</title>
        <style>
            body { font-family: sans-serif; text-align: center; background: #f0f2f5; padding: 40px; }
            .card { background: white; padding: 25px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 6px solid #28a745; min-width: 300px; }
            .buy { color: #28a745; font-weight: bold; }
            .sell { color: #dc3545; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>RELIANCE: <span style="color:#28a745;">ACTIVE</span></h2>
            <p><b>Market Scan At:</b> {{ last_time }}</p>
            <p><b>Signals Today:</b> {{ count }}</p>
            <hr>
            <h4>History:</h4>
            {% if history %}
                {% for s in history %}
                    <p class="{{ s.type.lower() }}">[{{ s.t }}] {{ s.type }} @ {{ s.p }}</p>
                {% endfor %}
            {% else %}
                <p style="color:gray;">कंडिशन मॅच होण्याची वाट पाहत आहे...</p>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, last_time=LAST_CHECK_TIME, count=len(SIGNAL_HISTORY), history=SIGNAL_HISTORY[::-1])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
