import os
import pytz
import requests
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- धन क्रेडेंशियल्स ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "sIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.7vA8iFqaDolR-4dHRnsbiLnHNMWDiiGe8N3J53vYOtw0wxhSWE4_MRNgvG6SGMNSy0pcREiWKHEtrhOZmT2KIA"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
IST = pytz.timezone('Asia/Kolkata')

# टेलिग्राम डिटेल्स
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# Crude Oil MCX डिटेल्स (March Future)
# टीप: दर महिन्याला 'sid' बदलावा लागू शकतो
CRUDE_OIL_LIST = [
    {'symbol': 'CRUDE OIL MAR FUT', 'sid': '420844'} # MCX मार्च फ्युचर आयडी
]

def send_signal(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=5)
    except: pass

def process_crude_strategy():
    results = {}
    today = datetime.now(IST).strftime('%Y-%m-%d')
    for item in CRUDE_OIL_LIST:
        try:
            # MCX साठी exchange_segment 'MCX_FO' वापरावा लागतो
            data = dhan.intraday_minute_data(item['sid'], 'MCX_FO', 'FUTIDX', today, today)
            if data and data.get('status') == 'success' and 'data' in data:
                d = data['data']
                ltp = d['close'][-1]
                results[item['symbol']] = ltp
                
                # बॉडी-टू-बॉडी ट्रेडिंग लॉजिक
                if len(d['close']) >= 2:
                    po, pc, cc = d['open'][-2], d['close'][-2], d['close'][-1]
                    if po > pc and cc > po:
                        send_signal(f"🛢️ *CRUDE OIL BUY*\nPrice: ₹{cc}")
                    elif pc > po and cc < po:
                        send_signal(f"🛢️ *CRUDE OIL SELL*\nPrice: ₹{cc}")
        except Exception as e:
            print(f"Error: {e}")
    return results

@app.route('/')
def home():
    prices = process_crude_strategy()
    now = datetime.now(IST).strftime('%H:%M:%S')
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head><meta http-equiv="refresh" content="30"><title>Crude Oil Bot</title></head>
    <body style="font-family:sans-serif; text-align:center; background:#2c3e50; color:white;">
        <div style="background:#34495e; padding:30px; border-radius:15px; display:inline-block; margin-top:50px; box-shadow:0 10px 20px rgba(0,0,0,0.5);">
            <h1 style="color:#f1c40f;">🛢️ Crude Oil Live</h1>
            <p>Last Sync: {{ last_time }}</p>
            <hr style="border:0; border-top:1px solid #7f8c8d;">
            {% for s, p in ltp.items() %}
                <div style="font-size:24px; margin:20px;">
                    <span>{{ s }}:</span> <b style="color:#2ecc71;">₹{{ p }}</b>
                </div>
            {% else %}
                <p>डेटा येत नाहीये. <br>MCX चा डेटा मिळवण्यासाठी धन वर MCX सेगमेंट चालू असल्याची खात्री करा.</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """, ltp=prices, last_time=now)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
