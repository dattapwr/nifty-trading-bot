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
ACCESS_TOKEN = "YOUR_NEW_TOKEN_HERE" # <--- तुमचा नवीन टोकन इथे टाका

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
LAST_CHECK_TIME = "प्रतीक्षा करत आहे..."

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
    send_telegram("✅ *Reliance Bot Online!* टेस्टिंग सुरू होत आहे...")
    
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

                # --- खालील लॉजिक फक्त टेस्टिंगसाठी दर मिनिटाला सिग्नल देईल ---
                # एकदा मेसेज यायला लागला की 'if True:' काढून मूळ लॉजिक टाका.
                if True: 
                    res = {
                        's': stock['symbol'], 
                        'p': "TESTING", 
                        'type': 'LIVE', 
                        't': now_ist.strftime('%H:%M:%S'),
                        'id_t': now_ist.strftime('%H%M')
                    }
                    # दर मिनिटाला नवीन मेसेज पाठवण्यासाठी जुना मेसेज चेक करणे बंद केले आहे
                    SIGNAL_HISTORY.append(res)
                    send_telegram(f"🔔 *System Test*\nStock: `{res['s']}`\nStatus: Bot is Active\nTime: {res['t']}")
                    print("Test signal sent to Telegram")

        except Exception as e:
            print(f"Loop Error: {e}")
        
        pytime.sleep(60) # दर ६० सेकंदाला चेक करा

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
            body { font-family: sans-serif; text-align: center; background: #eceff1; padding: 50px; }
            .card { background: white; padding: 30px; border-radius: 15px; display: inline-block; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
            .status-live { color: #2ecc71; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Reliance Bot: <span class="status-live">LIVE</span></h1>
            <p><b>Last Scan:</b> {{ last_time }}</p>
            <p><b>Signals Found:</b> {{ count }}</p>
            <hr>
            <h3>Recent Activity:</h3>
            {% for s in history[:5] %}
                <p>[{{ s.t }}] {{ s.s }} - {{ s.type }}</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, last_time=LAST_CHECK_TIME, count=len(SIGNAL_HISTORY), history=SIGNAL_HISTORY[::-1])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
