import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask, render_template_string

app = Flask(__name__)

# --- तुमची माहिती (Securely Added) ---
CLIENT_ID = "1105760761"
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

def get_slot_data(slot_time):
    """ठराविक स्लॉटसाठी API कडून डेटा खेचणे"""
    entry = {"time": slot_time, "crude": "NO DATA", "ng": "NO DATA", "c_price": "-", "n_price": "-"}
    
    for name, s_id in COMMODITIES.items():
        try:
            resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
            if resp and resp.get('status') == 'success':
                data = resp.get('data')
                if data and len(data) >= 1:
                    last_candle = data[-1]
                    status = "YES"
                    price = last_candle.get('close', '-')
                    
                    if name == 'CRUDEOIL':
                        entry["crude"] = status
                        entry["c_price"] = price
                    else:
                        entry["ng"] = status
                        entry["n_price"] = price
                    
                    # लेटेस्ट सिग्नल अपडेट (उदाहरणासाठी शेवटची किंमत दाखवणे)
                    global latest_signal
                    latest_signal = {"side": "LIVE", "stock": name, "price": price}
        except:
            pass
    return entry

def scanner():
    global status_log
    last_processed_slot = ""
    
    while True:
        now = datetime.now()
        # वेळेला १५ मिनिटांच्या टप्प्यात बसवणे (00, 15, 30, 45)
        rounded_min = (now.minute // 15) * 15
        slot_time = now.replace(minute=rounded_min, second=0).strftime('%I:%M %p')

        if slot_time != last_processed_slot:
            # सकाळी ९ ते रात्री ११:३० या वेळेतच रन करा
            if 9 <= now.hour <= 23:
                new_entry = get_slot_data(slot_time)
                status_log.insert(0, new_entry)
                status_log = status_log[:15] # शेवटचे १५ स्लॉट्स दाखवा
                
                # टेलिग्राम रिपोर्ट
                report = (f"📊 *MCX 15-Min Update*\n"
                          f"🕒 Time: {slot_time}\n"
                          f"🛢️ Crude: {new_entry['crude']} (₹{new_entry['c_price']})\n"
                          f"🔥 Nat Gas: {new_entry['ng']} (₹{new_entry['n_price']})")
                send_telegram(report)
                
                last_processed_slot = slot_time
        
        time.sleep(30) # दर ३० सेकंदाला नवीन स्लॉट आला का ते चेक करा

# --- HTML डिझाइन ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="mr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCX Live Monitor</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { background: #0b0e11; color: white; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .card { background: #1e2329; padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #2b3139; width: 90%; max-width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); margin-bottom: 30px; }
        .badge { background: #f0b90b; color: black; padding: 5px 12px; border-radius: 50px; font-weight: bold; font-size: 12px; text-transform: uppercase; }
        .price { font-size: 50px; font-weight: bold; margin: 15px 0; color: #f0b90b; }
        .stock { font-size: 18px; color: #848e9c; }
        
        table { width: 100%; max-width: 500px; border-collapse: collapse; background: #161b22; border-radius: 10px; overflow: hidden; border: 1px solid #30363d; }
        th, td { padding: 15px; text-align: center; border-bottom: 1px solid #30363d; }
        th { background: #21262d; color: #58a6ff; font-size: 14px; }
        .status-yes { color: #3fb950; font-weight: bold; }
        .time-col { color: #848e9c; font-weight: 500; }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">{{ signal.side }} SCANNING</div>
        <div class="stock">{{ signal.stock }}</div>
        <div class="price">{% if signal.price == 'Waiting' %}Waiting...{% else %}₹{{ signal.price }}{% endif %}</div>
        <div style="color: #474d57; font-size: 11px;">Updated at: {{ time }}</div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Time Slot</th>
                <th>Crude</th>
                <th>Nat Gas</th>
            </tr>
        </thead>
        <tbody>
            {% for log in logs %}
            <tr>
                <td class="time-col">{{ log.time }}</td>
                <td class="{% if log.crude == 'YES' %}status-yes{% endif %}">{{ log.crude }}</td>
                <td class="{% if log.ng == 'YES' %}status-yes{% endif %}">{{ log.ng }}</td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="color: #474d57;">डेटा गोळा होत आहे... पुढील १५ मिनिटांची प्रतीक्षा करा.</td></tr>
            {% endfor %}
        </tbody>
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
    # Render साठी पोर्ट सेटिंग
    port = int(os.environ.get("PORT", 10000))
    # स्कॅनर थ्रेड सुरू करणे
    Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
