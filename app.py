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
COMMODITIES = {'CRUDEOIL': 25145, 'NATURALGAS': 25147}

# डेटा ट्रॅकिंग
data_status = {'CRUDEOIL': 'Waiting...', 'NATURALGAS': 'Waiting...'}
status_log = [] # डॅशबोर्डवर दिवसभराचा इतिहास दाखवण्यासाठी
latest_signals_list = []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def scanner():
    global latest_signals_list, data_status, status_log
    send_telegram("🚀 *MCX लॉगिंग बॉट सुरू झाला!* \nआता तुम्हाला प्रत्येक १५ मिनिटांचा रिपोर्ट मिळेल.")
    
    last_logged_minute = -1
    
    while True:
        now = datetime.now()
        current_time_str = now.strftime('%H:%M')

        # मार्केट वेळ (MCX)
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            # प्रत्येक १५ मिनिटाला लॉग अपडेट करा (उदा. १०:००, १०:१५...)
            if now.minute % 15 == 0 and now.minute != last_logged_minute:
                log_entry = {"time": current_time_str, "crude": "Checking...", "ng": "Checking..."}
                
                telegram_report = f"📊 *MCX Report ({current_time_str}):*\n"
                
                for name, s_id in COMMODITIES.items():
                    try:
                        resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
                        if resp and resp.get('status') == 'success':
                            res_data = resp.get('data')
                            status = "Yes" if (res_data and len(res_data) >= 2) else "No Data"
                        else:
                            status = "No"
                    except:
                        status = "Error"
                    
                    data_status[name] = status
                    if name == 'CRUDEOIL': log_entry["crude"] = status
                    else: log_entry["ng"] = status
                    telegram_report += f"• {name}: {status}\n"
                
                # लॉग लिस्टमध्ये नवीन एंट्री वरती टाका
                status_log.insert(0, log_entry)
                status_log = status_log[:20] # फक्त शेवटच्या २० वेळा दाखवा
                
                send_telegram(telegram_report)
                last_logged_minute = now.minute

            # सिग्नल स्कॅनिंग (सतत सुरू राहील)
            for name, s_id in COMMODITIES.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if data and len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            # Body Breakout Logic
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['open']:
                                    sig_msg = f"🎯 *SELL:* {name} | Price: {curr['close']} | Time: {now.strftime('%H:%M:%S')}"
                                    if sig_msg not in latest_signals_list:
                                        latest_signals_list.insert(0, sig_msg)
                                        latest_signals_list = latest_signals_list[:5]
                                        send_telegram(sig_msg)
                except: continue
                time.sleep(1)
        else:
            for key in data_status: data_status[key] = "Market Closed"
            
        time.sleep(30)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MCX Day Log</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0d1117; color: white; padding: 20px; }
        .container { max-width: 600px; margin: auto; }
        .card { background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border: 1px solid #30363d; text-align: center; font-size: 14px; }
        th { background: #21262d; color: #58a6ff; }
        .yes { color: #3fb950; }
        .no { color: #f85149; }
        .no-data { color: #e3b341; }
        .signal { background: #d9534f; padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>📊 Live Status Log</h2>
            <p style="color: #8b949e; font-size: 12px;">येथे दर १५ मिनिटांची हिस्ट्री दिसेल</p>
            <table>
                <tr>
                    <th>Time</th>
                    <th>Crude Oil</th>
                    <th>Natural Gas</th>
                </tr>
                {% for entry in logs %}
                <tr>
                    <td>{{ entry.time }}</td>
                    <td class="{{ 'yes' if entry.crude=='Yes' else ('no-data' if entry.crude=='No Data' else 'no') }}">{{ entry.crude }}</td>
                    <td class="{{ 'yes' if entry.ng=='Yes' else ('no-data' if entry.ng=='No Data' else 'no') }}">{{ entry.ng }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h3>🎯 Latest Signals</h3>
            {% for s in signals %}
                <div class="signal">{{ s }}</div>
            {% else %}
                <p style="color: #8b949e;">No active signals.</p>
            {% endfor %}
        </div>
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
