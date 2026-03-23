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

# स्टेटस ट्रॅक करण्यासाठी (Yes / No / No Data)
data_status = {'CRUDEOIL': 'Waiting...', 'NATURALGAS': 'Waiting...'}
latest_signals_list = []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def scanner():
    global latest_signals_list, data_status
    send_telegram("🚀 *MCX १५ मिनिट बॉट (Status: No Data Option) सुरू झाला!*")
    
    while True:
        now = datetime.now()
        # MCX मार्केट वेळ
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            for name, s_id in COMMODITIES.items():
                try:
                    # १५ मिनिटांचा डेटा मागवत आहे
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15') 
                    
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if data and len(data) >= 2:
                            data_status[name] = "Yes"
                            prev, curr = data[-2], data[-1]
                            
                            # Body-to-Body Sell Logic (Red close < Green open)
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['open']:
                                    sig_msg = f"🎯 *15-MIN SELL:* {name} | Price: {curr['close']} | Time: {now.strftime('%H:%M:%S')}"
                                    if sig_msg not in latest_signals_list:
                                        latest_signals_list.insert(0, sig_msg)
                                        latest_signals_list = latest_signals_list[:5]
                                        send_telegram(sig_msg)
                        else:
                            data_status[name] = "No Data" # डेटा रिकामा आहे
                    else:
                        data_status[name] = "No" # प्रतिसाद मिळाला पण एरर आहे
                except Exception as e:
                    data_status[name] = "No Data" # कनेक्शन किंवा इतर एरर
                    continue
                time.sleep(2)
        else:
            # मार्केट बंद असताना स्टेटस
            for key in data_status: data_status[key] = "Market Closed"
            
        time.sleep(30)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MCX Live Monitor</title>
    <meta http-equiv="refresh" content="15">
    <style>
        body { font-family: 'Segoe UI', Arial; background-color: #0d1117; color: white; text-align: center; padding: 20px; }
        .dashboard { max-width: 500px; margin: auto; background: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .status-table { width: 100%; margin: 20px 0; border-collapse: collapse; }
        .status-table th, .status-table td { padding: 12px; border: 1px solid #30363d; text-align: center; }
        .yes { color: #3fb950; font-weight: bold; }
        .no { color: #f85149; font-weight: bold; }
        .no-data { color: #e3b341; font-weight: bold; }
        .signal-box { background: #d9534f; color: white; padding: 12px; margin: 8px 0; border-radius: 8px; text-align: left; font-size: 14px; border-left: 5px solid #fff; }
        h2 { color: #58a6ff; margin-bottom: 5px; }
        p.info { font-size: 12px; color: #8b949e; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h2>📊 MCX Live Monitor</h2>
        <p class="info">Timeframe: 15 Minutes | Auto-refresh: 15s</p>
        
        <table class="status-table">
            <thead>
                <tr><th>Symbol</th><th>Dhan Status</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td>CRUDE OIL</td>
                    <td class="{{ 'yes' if status['CRUDEOIL']=='Yes' else ('no-data' if status['CRUDEOIL']=='No Data' else 'no') }}">
                        {{ status['CRUDEOIL'] }}
                    </td>
                </tr>
                <tr>
                    <td>NATURAL GAS</td>
                    <td class="{{ 'yes' if status['NATURALGAS']=='Yes' else ('no-data' if status['NATURALGAS']=='No Data' else 'no') }}">
                        {{ status['NATURALGAS'] }}
                    </td>
                </tr>
            </tbody>
        </table>

        <hr style="border: 0.1px solid #30363d; margin: 20px 0;">
        
        <h3>Latest 15-Min Signals</h3>
        {% if signals %}
            {% for s in signals %}
                <div class="signal-box">{{ s }}</div>
            {% endfor %}
        {% else %}
            <p style="color: #8b949e; font-style: italic;">स्कॅनिंग सुरू आहे, सिग्नलची प्रतीक्षा करा...</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE, status=data_status, signals=latest_signals_list)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
