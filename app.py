import requests
import time
import threading
import json
from flask import Flask, render_template_string
from datetime import datetime, time as dt_time, timedelta

app = Flask(__name__)

# --- १. तुमची माहिती (Securely Added) ---
CLIENT_ID = "1105700701"
ACCESS_TOKEN = "तुमचा_Dhan_Token_इथे_टाका"
TELEGRAM_TOKEN = "8581468481:AAETOZPw9mptClRDOrvldCX_5oVmdgnkc9Y"
TELEGRAM_CHAT_ID = "799650120"

# --- २. सेटिंग्ज ---
TRADE_SIDE = "BUY"       # "BUY" किंवा "SELL"
MAX_TRADES = 10          # दिवसाची मर्यादा
SL_BUFFER_PCT = 0.0015   # 0.15% Buffer
LOG_FILE = "trade_signals.json"

# --- ३. १८० स्टॉक्सची लिस्ट (नमुना - येथे पूर्ण लिस्ट जोडा) ---
INSTRUMENTS = {
    'RELIANCE': '2885', 'SBIN': '3045', 'HDFCBANK': '1333', 'ICICIBANK': '4963',
    'INFY': '1594', 'TCS': '11536', 'ITC': '1660', 'AXISBANK': '5900',
    'KOTAKBANK': '1922', 'LT': '11483', 'BHARTIARTL': '10604', 'TATAMOTORS': '3456'
}

def load_logs():
    try:
        with open(LOG_FILE, "r") as f: return json.load(f)
    except: return []

def save_logs(logs):
    with open(LOG_FILE, "w") as f: json.dump(logs, f)

status_log = load_logs()
traded_today = []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def get_dhan_data(security_id, interval):
    url = "https://api.dhan.co/charts/historical" if interval == "1D" else "https://api.dhan.co/charts/intraday"
    headers = {"access-token": ACCESS_TOKEN, "Content-Type": "application/json"}
    payload = {
        "securityId": str(security_id), "exchangeSegment": "NSE_EQ", "instrumentType": "EQUITY",
        "fromDate": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        "toDate": datetime.now().strftime('%Y-%m-%d'), "interval": interval
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=8)
        return r.json().get('data', {}).get('candles', []) if r.status_code == 200 else None
    except: return None

def scanner():
    global status_log, traded_today
    send_telegram(f"🚀 **NSE स्टॉक स्कॅनर सुरू झाला!**\nमोड: {TRADE_SIDE}\nवेळ: सकाळी ९:३० ते दुपारी १:००")

    while True:
        now = datetime.now()
        
        # दररोज सकाळी ९ वाजता जुने सिग्नल्स साफ करणे
        if now.hour == 9 and now.minute == 0:
            status_log = []; traded_today = []; save_logs([])

        if now.time() < dt_time(9, 30) or now.time() > dt_time(13, 0) or len(traded_today) >= MAX_TRADES:
            time.sleep(60); continue

        for name, s_id in INSTRUMENTS.items():
            if name in traded_today: continue

            daily = get_dhan_data(s_id, "1D")
            intra = get_dhan_data(s_id, "5")
            if not daily or not intra or len(daily) < 2 or len(intra) < 2: continue

            y_open, y_close = daily[-2][1], daily[-2][4]
            t_open, ltp = intra[0][1], intra[-1][4]
            c_low, c_high = intra[-1][3], intra[-1][2]
            p_open, p_close = intra[-2][1], intra[-2][4]

            is_signal = False
            if TRADE_SIDE == "BUY":
                gap_up = ((t_open - y_close) / y_close) * 100
                if y_close > y_open and 0.1 <= gap_up <= 1.5:
                    if p_close < p_open and ltp > p_open:
                        entry, sl = ltp, c_low - (c_low * SL_BUFFER_PCT)
                        tgt = entry + (entry - sl) * 2
                        is_signal = True
            
            elif TRADE_SIDE == "SELL":
                gap_down = ((y_close - t_open) / y_close) * 100
                if y_close < y_open and 0.1 <= gap_down <= 1.5:
                    if p_close > p_open and ltp < p_open:
                        entry, sl = ltp, c_high + (c_high * SL_BUFFER_PCT)
                        tgt = entry - (sl - entry) * 2
                        is_signal = True

            if is_signal:
                traded_today.append(name)
                msg = f"🎯 **नवा सिग्नल: {name}**\nकिंमत: ₹{entry}\nSL: ₹{sl:.2f}\nTGT: ₹{tgt:.2f}"
                send_telegram(msg)
                
                status_log.insert(0, {"time": now.strftime('%H:%M'), "stock": name, "status": f"{TRADE_SIDE} @ {entry}"})
                save_logs(status_log)
                if len(traded_today) >= MAX_TRADES: break
            time.sleep(0.6)
        time.sleep(30)

@app.route('/')
def home():
    # हा HTML तुमच्या डॅशबोर्डवर सिग्नल दाखवेल
    table_rows = "".join([f"<tr><td>{l['time']}</td><td>{l['stock']}</td><td>{l['status']}</td></tr>" for l in status_log])
    return render_template_string("""
        <body style="background:#111; color:white; font-family:sans-serif; text-align:center;">
            <h2>📊 NSE MONITOR</h2>
            <table border="1" style="margin:auto; width:80%; border-collapse:collapse;">
                <tr style="background:#333;"><th>Time</th><th>Stock</th><th>Signal</th></tr>
                {{ rows|safe }}
            </table>
            <script>setTimeout(lambda: location.reload(), 30000);</script>
        </body>
    """, rows=table_rows if table_rows else "<tr><td colspan='3'>Waiting for signals...</td></tr>")

if __name__ == "__main__":
    threading.Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
