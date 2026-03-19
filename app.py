
import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स (Updated Token) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "EyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzczOTk1NDIwLCJpYXQiOjE3NzM5MDkwMjAsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.tY2eexkpvfD2DLJxEWM9-67HY2sVhbBtHIuEKCmIIGlnhbpeUM5N5uwQJgH-2Hlib7APt6Lc8RP4rHI6gpmY1A"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
LAST_CHECK_TIME = "प्रतीक्षा करत आहे..."
DATA_STATUS = "सुरू होत आहे..."
CURRENT_LTP = {}

# २० प्रमुख स्टॉक्सची यादी
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
    global LAST_CHECK_TIME, DATA_STATUS
    now_ist = datetime.now(IST)
    LAST_CHECK_TIME = now_ist.strftime('%H:%M:%S')
    today = now_ist.strftime('%Y-%m-%d')
    
    found_any_data = False
    for stock in WATCHLIST:
        try:
            data = dhan.intraday_minute_data(
                security_id=stock['sid'], exchange_segment='NSE_EQ',
                instrument_type='EQUITY', from_date=today, to_date=today
            )
            
            if data and data.get('status') == 'success':
                found_any_data = True
                d = data.get('data', {})
                if d and 'close' in d and len(d['close']) > 0:
                    cc = d['close'][-1]
                    CURRENT_LTP[stock['symbol']] = cc
                    
                    # बॉडी-टू-बॉडी ट्रेडिंग लॉजिक (५ मिनिटे)
                    if len(d['close']) >= 2:
                        po, pc = d['open'][-2], d['close'][-2]
                        cid = d['start_Time'][-1]
                        
                        res = None
                        if po > pc and cc > po: res = 'BUY'
                        elif pc > po and cc < po: res = 'SELL'
                        
                        if res and not any(x['s'] == stock['symbol'] and x['id_t'] == cid for x in SIGNAL_HISTORY):
                            msg = f"{'🟢' if res=='BUY' else '🔴'} *{res} SIGNAL*\nStock: `{stock['symbol']}`\nPrice: ₹{cc}"
                            requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}&parse_mode=Markdown", timeout=5)
                            SIGNAL_HISTORY.append({'s': stock['symbol'], 'p': cc, 'type': res, 't': LAST_CHECK_TIME, 'id_t': cid})
            
            pytime.sleep(0.3) # API Rate Limit टाळण्यासाठी
            
        except Exception:
            continue

    DATA_STATUS = "Connected ✅" if found_any_data else "API Error ❌"

def background_loop():
    # बोट सुरू झाल्याचा मेसेज
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text=🚀 *Scanner Live with 20 Stocks!*", timeout=5)
    while True:
        scan_markets()
        pytime.sleep(60)

# बॅकग्राउंड थ्रेड सुरू करा
threading.Thread(target=background_loop, daemon=True).start()

@app.route('/')
def home():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="30">
        <title>20 Stocks Live Scanner</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; text-align: center; background: #f0f2f5; margin: 0; padding: 20px; }
            .container { background: white; max-width: 600px; margin: auto; padding: 20px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
            .status-bar { padding: 10px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; font-size: 14px; }
            .online { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .offline { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 20px; }
            .stock-card { background: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; font-size: 13px; text-align: left; }
            .buy { color: #28a745; font-weight: bold; }
            .sell { color: #dc3545; font-weight: bold; }
            h2 { color: #333; margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📈 20 Stocks Scanner</h2>
            <div class="status-bar {% if '✅' in status %} online {% else %} offline {% endif %}">
                Status: {{ status }} | Last Scan: {{ last_time }}
            </div>
            
            <div class="grid">
                {% for s, p in ltp.items() %}
                    <div class="stock-card"><b>{{ s }}</b>: ₹{{ p }}</div>
                {% endfor %}
            </div>

            <hr style="border:0; border-top:1px solid #eee;">
            <h3>Latest Signals</h3>
            {% for s in history %}
                <p class="{{ s.type.lower() }}">[{{ s.t }}] {{ s.s }} - {{ s.type }} @ ₹{{ s.p }}</p>
            {% else %}
                <p style="color: #666; font-style: italic;">सिग्नलची वाट पाहत आहे...</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, last_time=LAST_CHECK_TIME, ltp=CURRENT_LTP, history=SIGNAL_HISTORY[::-1], status=DATA_STATUS)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
