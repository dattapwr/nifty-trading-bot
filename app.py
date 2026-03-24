import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask, render_template_string

app = Flask(__name__)

# --- तुमची माहिती भरा ---
CLIENT_ID = "तुमचा_CLIENT_ID"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0NDM0NDc0LCJpYXQiOjE3NzQzNDgwNzQsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.OyMxZqT_w_sbgtowNA0bOuF53vqIDL1bvKD-oAN0HN6Vl0zAaTwhKzh2KFF2OJocynHpZKBQj9o3WZmCHTn2ZA"
TELEGRAM_TOKEN = "8581468481:AAETOZPw9mptClRDOrvldCX_5oVmdgnkc9Y"
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

# डेटा साठवण्यासाठी ग्लोबल लिस्ट
status_log = [] 
latest_signal = {"side": "SCANNING", "stock": "MCX MONITOR", "price": "Waiting"}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_slot_data():
    """दर १५ मिनिटांनी डेटा मिळवते"""
    now = datetime.now()
    slot_time = now.strftime('%H:%M')
    
    entry = {"time": slot_time, "crude": "NO DATA", "ng": "NO DATA"}
    
    for name, s_id in COMMODITIES.items():
        try:
            # धन API कडून इंट्राडे डेटा मागवणे
            resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
            if resp and resp.get('status') == 'success':
                data = resp.get('data')
                if data and len(data) >= 2:
                    entry[name.lower().replace("oil","")] = "YES"
                    # सिग्नल चेकिंग (उदाहरणादाखल सेल सिग्नल)
                    curr = data[-1]
                    prev = data[-2]
                    if curr['close'] < prev['low']: # साधे लॉजिक
                        global latest_signal
                        latest_signal = {
                            "side": "SELL",
                            "stock": name,
                            "price": curr['close']
                        }
        except:
            entry[name.lower().replace("oil","")] = "ERROR"
            
    return entry

def scanner():
    global status_log
    last_processed_minute = -1
    
    while True:
        now = datetime.now()
        # दर १५ मिनिटांनी (उदा. 00, 15, 30, 45) रन होईल
        if now.minute % 15 == 0 and now.minute != last_processed_minute:
            new_entry = get_slot_data()
            status_log.insert(0, new_entry)
            status_log = status_log[:10] # फक्त शेवटचे १० रेकॉर्ड ठेवा
            
            # टेलिग्राम रिपोर्ट
            report = f"📊 *MCX 15-Min Report ({new_entry['time']})*\n• Crude: {new_entry['crude']}\n• NG: {new_entry['ng']}"
            send_telegram(report)
            
            last_processed_minute = now.minute
        
        time.sleep(30) # दर ३० सेकंदाला चेक करा

# --- प्रीमियम डेस्कटॉप डिझाइन (HTML) ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dhan AI Live Scanner</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { background: #0b0e11; color: white; font-family: sans-serif; margin: 0; display: flex; flex-direction: column; align-items: center; padding-top: 50px; }
        .card { background: #1e2329; padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #2b3139; width: 350px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .badge { background: #f0b90b; color: black; padding: 5px 15px; border-radius: 50px; font-weight: bold; font-size: 12px; }
        .price { font-size: 60px; font-weight: bold; margin: 20px 0; color: {% if signal.side == 'SELL' %}#f6465d{% else %}#f0b90b{% endif %}; }
        .stock { font-size: 20px; color: #848e9c; letter-spacing: 2px; }
        table { margin-top: 30px; width: 100%; max-width: 500px; border-collapse: collapse; background: #161b22; border-radius: 10px; overflow: hidden; }
        th, td { padding: 12px; text-align: center; border-bottom: 1px solid #30363d; }
        th { background: #21262d; color: #58a6ff; }
        .status-yes { color: #3fb950; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">{{ signal.side }} SIGNAL</div>
        <div class="stock">{{ signal.stock }}</div>
        <div class="price">₹{{ signal.price }}</div>
        <div style="color: #848e9c; font-size: 12px;">Last Update: {{ time }}</div>
    </div>

    <table>
        <tr>
            <th>Time Slot</th>
            <th>Crude</th>
            <th>Nat Gas</th>
        </tr>
        {% for log in logs %}
        <tr>
            <td>{{ log.time }}</td>
            <td class="{% if log.crude == 'YES' %}status-yes{% endif %}">{{ log.crude }}</td>
            <td class="{% if log.ng == 'YES' %}status-yes{% endif %}">{{ log.ng }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE, 
                                 signal=latest_signal, 
                                 logs=status_log, 
                                 time=datetime.now().strftime('%H:%M:%S'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
