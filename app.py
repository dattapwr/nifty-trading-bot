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
TELEGRAM_CHAT_ID = "799650120"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# एप्रिल एक्सपायरीसाठी नवीन IDs (कृपया हे मार्केट सुरू झाल्यावर एकदा तपासा)
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

data_status = {'CRUDEOIL': 'Waiting...', 'NATURALGAS': 'Waiting...'}
status_log = [] 
latest_signals_list = []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def scanner():
    global latest_signals_list, data_status, status_log
    send_telegram("🚀 *MCX १५-मिनिट लॉगिंग सिस्टीम सक्रिय!*")
    
    last_check_time = ""
    
    while True:
        now = datetime.now()
        # दर १५ मिनिटांचा टप्पा (00, 15, 30, 45)
        current_minute_slot = (now.minute // 15) * 15
        time_label = now.replace(minute=current_minute_slot, second=0).strftime('%H:%M')

        # मार्केट वेळ (MCX: 9 AM to 11:30 PM)
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            if time_label != last_check_time:
                current_entry = {"time": time_label, "crude": "Waiting...", "ng": "Waiting..."}
                telegram_rep = f"📊 *MCX Report ({time_label}):*\n"
                
                for name, s_id in COMMODITIES.items():
                    try:
                        # १५ मिनिटांचा डेटा
                        resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
                        if resp and resp.get('status') == 'success':
                            res_data = resp.get('data')
                            status = "Yes" if (res_data and len(res_data) >= 2) else "No Data"
                        else:
                            status = "No"
                    except:
                        status = "Error"
                    
                    data_status[name] = status
                    if name == 'CRUDEOIL': current_entry["crude"] = status
                    else: current_entry["ng"] = status
                    telegram_rep += f"• {name}: {status}\n"

                status_log.insert(0, current_entry)
                status_log = status_log[:15]
                send_telegram(telegram_rep)
                last_check_time = time_label

            # सिग्नल स्कॅनिंग
            for name, s_id in COMMODITIES.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if data and len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            # Body breakout logic
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['open']:
                                    sig = f"🎯 *SELL:* {name} | Price: {curr['close']} | Time: {now.strftime('%H:%M:%S')}"
                                    if sig not in latest_signals_list:
                                        latest_signals_list.insert(0, sig)
                                        latest_signals_list = latest_signals_list[:5]
                                        send_telegram(sig)
                except: continue
                time.sleep(1)
        else:
            # मार्केट बंद असतानाचा स्टेटस
            data_status['CRUDEOIL'] = "Market Closed"
            data_status['NATURALGAS'] = "Market Closed"
            
        time.sleep(30)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MCX Live Monitor</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: sans-serif; background-color: #0d1117; color: white; padding: 20px; }
        .box { max-width: 600px; margin: auto; background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; border: 1px solid #30363d; text-align: center; }
        .yes { color: #3fb950; font-weight: bold; }
        .no { color: #f85149; font-weight: bold; }
        .no-data { color: #e3b341; font-weight: bold; }
        .sig { background: #d9534f; padding: 10px; border-radius: 6px; margin-top: 5px; text-align: left; }
    </style>
</head>
<body>
    <div class="box">
        <h3>📊 15-Min Status History</h3>
        <table>
            <tr style="background: #21262d;">
                <th>Time Slot</th>
                <th>Crude Oil</th>
                <th>Natural Gas</th>
            </tr>
            {% for entry in logs %}
            <tr>
                <td>{{ entry.time }}</td>
                <td class="{{ 'yes' if entry.crude=='Yes' else ('no-data' if entry.crude=='No Data' else 'no') }}">{{ entry.crude }}</td>
                <td class="{{ 'yes' if entry.ng=='Yes' else ('no-data' if entry.ng=='No Data' else 'no') }}">{{ entry.ng }}</td>
            </tr>
            {% else %}
            <tr><td colspan="3">स्कॅनिंग सुरू होण्याची प्रतीक्षा करा (दर १५ मिनिटांनी अपडेट होईल)</td></tr>
            {% endfor %}
        </table>
        <hr style="border: 0.1px solid #333; margin: 20px 0;">
        <h3>🎯 Latest Signals</h3>
        {% for s in signals %}
            <div class="sig">{{ s }}</div>
        {% else %}
            <p style="color: #8b949e;">सध्या कोणताही सेल सिग्नल नाही.</p>
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
    Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
