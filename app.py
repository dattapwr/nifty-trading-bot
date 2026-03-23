import os
import requests
import time
from datetime import datetime
from dhanhq import dhanhq
from threading import Thread
from flask import Flask, render_template_string

app = Flask(__name__)

# --- तुमची माहिती ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "EyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MzY1MTg4LCJpYXQiOjE3NzQyNzg3ODgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.MYos_aoKx0Asovh4abb8mf-uiD7mNfY_-bVaq1YWNvJRpYrI_UBhJhZreE4TZ5uFgBZ_EmYLJ7avrDRbBeztAA"
TELEGRAM_TOKEN = "8581468481:AAGSx4vbYZ2Ygq_slm3PDpZBUzlcpWHsiAk"
TELEGRAM_CHAT_ID = "799650120" # तुमच्या टेलिग्राम आयडीनुसार

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

data_status = {'CRUDEOIL': 'Checking...', 'NATURALGAS': 'Checking...'}
status_log = [] 
latest_signals_list = []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_data_from_dhan():
    global data_status, status_log
    now = datetime.now()
    time_label = now.strftime('%H:%M')
    current_entry = {"time": time_label, "crude": "Waiting...", "ng": "Waiting..."}
    telegram_rep = f"📊 *MCX Status Report ({time_label}):*\n"
    
    for name, s_id in COMMODITIES.items():
        try:
            resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
            if resp and resp.get('status') == 'success':
                res_data = resp.get('data')
                status = "Yes" if (res_data and len(res_data) >= 2) else "No Data"
            else:
                status = "No"
        except Exception:
            status = "Error"
        
        data_status[name] = status
        if name == 'CRUDEOIL': current_entry["crude"] = status
        else: current_entry["ng"] = status
        telegram_rep += f"• {name}: {status}\n"

    status_log.insert(0, current_entry)
    if len(status_log) > 15:
        status_log = status_log[:15]
    return telegram_rep

def scanner():
    print("Scanner thread started...")
    last_check_time = ""
    
    # सुरुवातीला एकदा चेक करा
    try:
        initial_rep = get_data_from_dhan()
        send_telegram("🚀 *सिस्टीम रीस्टार्ट झाली आहे!*\n" + initial_rep)
    except Exception as e:
        print(f"Initial scan error: {e}")

    while True:
        try:
            now = datetime.now()
            # १५ मिनिटांचा स्लॉट चेक करा
            current_minute_slot = (now.minute // 15) * 15
            time_label = now.replace(minute=current_minute_slot, second=0).strftime('%H:%M')

            # MCX मार्केट वेळ (सकाळी ९ ते रात्री ११:३०)
            if (9, 0) <= (now.hour, now.minute) <= (23, 30):
                if time_label != last_check_time:
                    report = get_data_from_dhan()
                    send_telegram(report)
                    last_check_time = time_label

                # सेल सिग्नल लॉजिक
                for name, s_id in COMMODITIES.items():
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if data and len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            # Body breakout logic
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['open']:
                                    sig = f"🎯 *SELL SIGNAL:* {name}\n💰 Price: {curr['close']}\n⏰ Time: {now.strftime('%H:%M:%S')}"
                                    if sig not in latest_signals_list:
                                        latest_signals_list.insert(0, sig)
                                        if len(latest_signals_list) > 5:
                                            latest_signals_list = latest_signals_list[:5]
                                        send_telegram(sig)
            else:
                for k in data_status: data_status[k] = "Market Closed"
        except Exception as e:
            print(f"Scanner Loop Error: {e}")
            
        time.sleep(30) # ३० सेकंदाचा गॅप

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MCX Live Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0d1117; color: white; padding: 20px; text-align: center; }
        .box { max-width: 600px; margin: auto; background: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; border: 1px solid #30363d; text-align: center; }
        th { background-color: #21262d; color: #58a6ff; }
        .yes { color: #3fb950; font-weight: bold; }
        .no-data { color: #e3b341; font-weight: bold; }
        .market-closed { color: #8b949e; }
        .sig { background: #d9534f; padding: 12px; border-radius: 8px; margin-top: 10px; text-align: left; border-left: 6px solid #fff; font-size: 14px; }
        h2 { margin-top: 0; color: #f0f6fc; }
    </style>
</head>
<body>
    <div class="box">
        <h2>📊 MCX Status History</h2>
        <table>
            <tr>
                <th>Time Slot</th>
                <th>Crude Oil</th>
                <th>Natural Gas</th>
            </tr>
            {% for entry in logs %}
            <tr>
                <td>{{ entry.time }}</td>
                <td class="{{ 'yes' if entry.crude=='Yes' else ('no-data' if entry.crude=='No Data' else 'market-closed') }}">{{ entry.crude }}</td>
                <td class="{{ 'yes' if entry.ng=='Yes' else ('no-data' if entry.ng=='No Data' else 'market-closed') }}">{{ entry.ng }}</td>
            </tr>
            {% else %}
            <tr><td colspan="3">सिस्टीम कनेक्ट होत आहे... कृपया थोडा वेळ थांबा.</td></tr>
            {% endfor %}
        </table>
        <hr style="border: 0.1px solid #30363d; margin: 25px 0;">
        <h3>🎯 Latest Sell Signals</h3>
        {% for s in signals %}
            <div class="sig">{{ s | replace('\\n', '<br>') | safe }}</div>
        {% else %}
            <p style="color: #8b949e; font-style: italic;">सध्या कोणताही सिग्नल उपलब्ध नाही.</p>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE, logs=status_log, signals=latest_signals_list)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # थ्रेड सुरू करण्यापूर्वी प्रिंट करा जेणेकरून लॉगमध्ये दिसेल
    t = Thread(target=scanner, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=port)
