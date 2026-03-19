import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स (सुरक्षेसाठी टोकन कोणालाही देऊ नका) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "YOUR_NEW_TOKEN_HERE" # <--- तुमचा नवीन टोकन इथे टाका

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
LAST_CHECK_TIME = "Checking..."

# --- २० टॉप स्टॉक्सची यादी ---
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
    try: 
        requests.get(url, params=params, timeout=10)
    except: 
        pass

def check_strategy_loop():
    global LAST_CHECK_TIME
    send_telegram("🚀 *20 Stocks Scanner Active!* \nMonitoring NSE Market...")
    
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
                except:
                    continue # एरर आल्यास पुढच्या स्टॉककडे जा

                if data and data.get('status') == 'success' and 'data' in data:
                    d = data['data']
                    if 'open' in d and len(d['open']) >= 2:
                        prev_o = float(d['open'][-2])
                        prev_c = float(d['close'][-2])
                        curr_c = float(d['close'][-1])
                        candle_id = d['start_Time'][-1]
                        
                        res = None
                        # --- मुख्य ट्रेडिंग लॉजिक ---
                        if prev_o > prev_c and curr_c > prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'BUY'}
                        elif prev_c > prev_o and curr_c < prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'SELL'}

                        if res:
                            # डुप्लिकेट चेक
                            if not any(x['s'] == res['s'] and x['id_t'] == candle_id for x in SIGNAL_HISTORY):
                                res['t'] = now_ist.strftime('%H:%M:%S')
                                res['id_t'] = candle_id
                                SIGNAL_HISTORY.append(res)
                                icon = "🟢" if res['type'] == "BUY" else "🔴"
                                send_telegram(f"{icon} *{res['type']} ALERT*\n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")

                pytime.sleep(0.5) # धन API चा वेग सांभाळण्यासाठी गॅप

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
        <title>20 Stock Scanner</title>
        <style>
            body { font-family: sans-serif; text-align: center; background: #f0f2f5; padding: 30px; }
            .card { background: white; padding: 25px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 6px solid #007bff; min-width: 350px; }
            .buy { color: #28a745; font-weight: bold; }
            .sell { color: #dc3545; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border-bottom: 1px solid #ddd; padding: 8px; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Market Scanner: <span style="color:#007bff;">LIVE</span></h2>
            <p><b>Last Scan:</b> {{ last_time }} | <b>Total:</b> {{ count }}</p>
            <hr>
            <table>
                <tr><th>Time</th><th>Stock</th><th>Type</th><th>Price</th></tr>
                {% for s in history %}
                    <tr class="{{ s.type.lower() }}">
                        <td>{{ s.t }}</td><td>{{ s.s }}</td><td>{{ s.type }}</td><td>{{ s.p }}</td>
                    </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, last_time=LAST_CHECK_TIME, count=len(SIGNAL_HISTORY), history=SIGNAL_HISTORY[::-1])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
