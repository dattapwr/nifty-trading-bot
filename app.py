import os
import pytz
import requests
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- धन क्रेडेंशियल्स ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MDAwNTY0LCJpYXQiOjE3NzM5MTQxNjQsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.7vA8iFqaDolR-4dHRnsbiLnHNMWDiiGe8N3J53vYOtw0wxhSWE4_MRNgvG6SGMNSy0pcREiWKHEtrhOZmT2KIA"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
IST = pytz.timezone('Asia/Kolkata')

WATCHLIST = [
    {'symbol': 'RELIANCE', 'sid': '2885'}, {'symbol': 'TCS', 'sid': '11536'},
    {'symbol': 'HDFCBANK', 'sid': '1333'}, {'symbol': 'ICICIBANK', 'sid': '4963'},
    {'symbol': 'INFY', 'sid': '1594'}, {'symbol': 'SBIN', 'sid': '3045'},
    {'symbol': 'BHARTIARTL', 'sid': '10604'}, {'symbol': 'LICI', 'sid': '11802'},
    {'symbol': 'ITC', 'sid': '1660'}, {'symbol': 'HINDUNILVR', 'sid': '1394'}
]

def get_live_data():
    results = {}
    today = datetime.now(IST).strftime('%Y-%m-%d')
    for stock in WATCHLIST:
        try:
            data = dhan.intraday_minute_data(stock['sid'], 'NSE_EQ', 'EQUITY', today, today)
            if data and data.get('status') == 'success':
                results[stock['symbol']] = data['data']['close'][-1]
        except:
            continue
    return results

@app.route('/')
def home():
    prices = get_live_data() # पेज लोड होताच डेटा खेचणे
    now = datetime.now(IST).strftime('%H:%M:%S')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="30">
        <title>Live Scanner</title>
        <style>
            body { font-family: sans-serif; text-align: center; background: #f4f7f6; padding: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; width: 100%; max-width: 400px; }
            .item { display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #eee; }
            .online { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>📈 Live Prices <span class="online">●</span></h2>
            <p>Last Sync: {{ last_time }}</p>
            <hr>
            {% for s, p in ltp.items() %}
                <div class="item"><span>{{ s }}</span> <b>₹{{ p }}</b></div>
            {% else %}
                <p>डेटा मिळत नाहीये. कृपया टोकन तपासा.</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, ltp=prices, last_time=now)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
