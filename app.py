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

# स्टेटस लॉग साठवण्यासाठी लिस्ट
status_log = [] 
latest_signals_list = []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_slot_status():
    """दर १५ मिनिटांनी डेटा तपासून स्टेटस तयार करते"""
    now = datetime.now()
    # १५ मिनिटांचा टप्पा ठरवणे (उदा. 10:00, 10:15)
    current_minute = (now.minute // 15) * 15
    time_label = now.replace(minute=current_minute, second=0).strftime('%H:%M')
    
    entry = {"time": time_label, "crude": "Checking...", "ng": "Checking..."}
    
    for name, s_id in COMMODITIES.items():
        try:
            resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
            if resp and resp.get('status') == 'success':
                res_data = resp.get('data')
                # जर डेटा असेल तर YES, नसेल तर NO DATA
                status = "YES" if (res_data and len(res_data) >= 2) else "NO DATA"
            else:
                status = "NO"
        except:
            status = "ERROR"
        
        if name == 'CRUDEOIL': entry["crude"] = status
        else: entry["ng"] = status
        
    return entry

def scanner():
    global status_log, latest_signals_list
    last_processed_slot = ""
    
    while True:
        now = datetime.now()
        # दर १५ मिनिटांचा स्लॉट ओळखा
        current_slot = (now.minute // 15) * 15
        slot_time = now.replace(minute=current_slot, second=0).strftime('%H:%M')

        # मार्केट वेळेतच चेक करा (9 AM to 11:30 PM)
        if (9, 0) <= (now.hour, now.minute) <= (23, 30):
            if slot_time != last_processed_slot:
                # नवीन स्लॉट सुरू झाल्यावर स्टेटस चेक करा
                new_entry = get_slot_status()
                status_log.insert(0, new_entry) # सर्वात नवीन वर दिसेल
                
                # फक्त शेवटचे १५ रेकॉर्ड ठेवा
                if len(status_log) > 15:
                    status_log = status_log[:15]
                
                # टेलिग्रामवर रिपोर्ट पाठवा
                report_msg = f"📊 *Slot Report ({slot_time}):*\n• Crude: {new_entry['crude']}\n• NG: {new_entry['ng']}"
                send_telegram(report_msg)
                
                last_processed_slot = slot_time

            # सेल सिग्नलसाठी सतत स्कॅनिंग (प्रत्येक ३० सेकंदाला)
            for name, s_id in COMMODITIES.items():
                try:
                    resp = dhan.historical_minute_charts(s_id, 'MCX', 'INTRA', '15')
                    if resp and resp.get('status') == 'success':
                        data = resp.get('data')
                        if data and len(data) >= 2:
                            prev, curr = data[-2], data[-1]
                            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                                if curr['close'] < prev['open']:
                                    sig = f"🎯 *SELL SIGNAL:* {name}\nPrice: {curr['close']}\nTime: {now.strftime('%H:%M:%S')}"
                                    if sig not in latest_signals_list:
                                        latest_signals_list.insert(0, sig)
                                        latest_signals_list = latest_signals_list[:5]
                                        send_telegram(sig)
                except: pass
                
        time.sleep(30)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MCX 15-Min Monitor</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: sans-serif; background-color: #0d1117; color: white; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border: 1px solid #30363d; text-align: center; }
        th { background: #21262d; color: #58a6ff; }
        .yes { color: #3fb950; font-weight: bold; }
        .no { color: #f85149; font-weight: bold; }
        .nodata { color: #e3b341; font-weight: bold; }
        .signal-box { background: #d9534f; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align: center;">📊 MCX 15-Min Status History</h2>
        <table>
            <tr>
                <th>Time Slot</th>
                <th>Crude Oil</th>
                <th>Natural Gas</th>
            </tr>
            {% for log in logs %}
            <tr>
                <td>{{ log.time }}</td>
                <td class="{{ 'yes' if log.crude=='YES' else ('nodata' if log.crude=='NO DATA' else 'no') }}">{{ log.crude }}</td>
                <td class="{{ 'yes' if log.ng=='YES' else ('nodata' if log.ng=='NO DATA' else 'no') }}">{{ log.ng }}</td>
            </tr>
            {% else %}
            <tr><td colspan="3">डेटा गोळा होत आहे... पुढील १५ मिनिटांच्या स्लॉटची प्रतीक्षा करा.</td></tr>
            {% endfor %}
        </table>
        
        <h3 style="margin-top: 30px;">🎯 Latest Signals</h3>
        {% for s in signals %}
            <div class="signal-box">{{ s | replace('\\n', '<br>') | safe }}</div>
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
