import requests
import time
import threading
import json
from flask import Flask, render_template_string
from datetime import datetime, time as dt_time, timedelta

app = Flask(__name__)

# --- १. तुमची माहिती (येथे अपडेट करा) ---
CLIENT_ID = "1105700701"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0NTgxMjU0LCJpYXQiOjE3NzQ0OTQ4NTQsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.cwygeAQV84d2vRmMMDpOv_h_L2x69cO-fwXjWdDXuw2HTOF-HS-KokXVr0IrEr1V1vR8JkSV_WWDO5mlAgI2Iw"
TELEGRAM_TOKEN = "8581468481:AAETOZPw9mptClRDOrvldCX_5oVmdgnkc9Y"
TELEGRAM_CHAT_ID = "799650120"

# --- २. सेटिंग्ज ---
TRADE_SIDE = "BUY"       # "BUY" किंवा "SELL"
MAX_TRADES = 10          
SL_BUFFER_PCT = 0.0015   
LOG_FILE = "trade_signals.json"

# --- ३. १८०+ NSE स्टॉक्सची लिस्ट (Dhan IDs) ---
INSTRUMENTS = {
    'ACC': '22', 'AUBANK': '21238', 'ABBOTINDIA': '100', 'ADANIENT': '25', 'ADANIPORTS': '15083',
    'ADANIPOWER': '15060', 'ATGL': '17963', 'ABCAPITAL': '21205', 'ABFRL': '21035', 'ALKEM': '11703',
    'AMBUJACEM': '1270', 'APOLLOHOSP': '157', 'APOLLOTYRE': '163', 'ASHOKLEY': '212', 'ASIANPAINT': '236',
    'ASTRAL': '14418', 'AUROPHARMA': '275', 'AXISBANK': '5900', 'BAJAJ-AUTO': '16669', 'BAJFINANCE': '317',
    'BAJAJFINSV': '16675', 'BAJAJHLDNG': '304', 'BALKRISIND': '335', 'BANDHANBNK': '22639', 'BANKBARODA': '4668',
    'BANKINDIA': '4705', 'BATAINDIA': '371', 'BERGEPAINT': '404', 'BEL': '383', 'BHARATFORG': '422',
    'BPCL': '526', 'BHARTIARTL': '10604', 'BIOCON': '11373', 'BOSCHLTD': '2181', 'BRITANNIA': '547',
    'CANBK': '10794', 'CHOLAFIN': '685', 'CIPLA': '694', 'COALINDIA': '20374', 'COFORGE': '11543',
    'COLPAL': '15141', 'CONCOR': '4740', 'COROMANDEL': '739', 'CROMPTON': '17094', 'CUMMINSIND': '1901',
    'DABUR': '772', 'DALBHARAT': '8075', 'DEEPAKNTR': '19943', 'DELHIVERY': '18143', 'DIVISLAB': '10940',
    'DIXON': '21690', 'DLF': '14732', 'DRREDDY': '881', 'EICHERMOT': '910', 'ESCORTS': '951',
    'EXIDEIND': '971', 'FEDERALBNK': '1023', 'FORTIS': '12640', 'GAIL': '4738', 'GLAND': '18506',
    'GLENMARK': '7406', 'GMRINFRA': '13528', 'GODREJCP': '10099', 'GODREJPROP': '17875', 'GRASIM': '1232',
    'GUJGASLTD': '10599', 'HAL': '2303', 'HCLTECH': '7229', 'HDFCBANK': '1333', 'HDFCLIFE': '467',
    'HEROMOTOCO': '1348', 'HINDALCO': '1363', 'HINDCOPPER': '3212', 'HINDPETRO': '1406', 'HINDUNILVR': '1394',
    'ICICIBANK': '4963', 'ICICIGI': '21770', 'ICICIPRULI': '21085', 'IDFCFIRSTB': '11184', 'ITC': '1660',
    'INDIAMART': '10726', 'INDIHOTEL': '1515', 'IOC': '1624', 'IRCTC': '13611', 'IRFC': '160',
    'IGL': '11262', 'INDUSTOWER': '29135', 'INDUSINDBK': '5258', 'NAUKRI': '11023', 'INFY': '1594',
    'INDIGO': '11195', 'IPCALAB': '1633', 'JSWSTEEL': '11723', 'JINDALSTEL': '1722', 'JUBLFOOD': '18096',
    'KOTAKBANK': '1922', 'L&TFH': '249', 'LT': '11483', 'LTIM': '17818', 'LTTS': '18564',
    'LICHSGFIN': '1997', 'LUPIN': '2014', 'M&M': '2031', 'M&MFIN': '13285', 'MARICO': '15135',
    'MARUTI': '10999', 'MAXHEALTH': '13147', 'METROBRAND': '256', 'MPHASIS': '4503', 'MRF': '2277',
    'MUTHOOTFIN': '23650', 'NYKAA': '411', 'NTPC': '11630', 'NESTLEIND': '17963', 'NMDC': '15332',
    'ONGC': '2475', 'OFSS': '10738', 'PAYTM': '1250', 'PIIND': '2412', 'PIDILITIND': '2424',
    'POLYCAB': '13786', 'POWERTAR': '14977', 'PFC': '14299', 'PGHH': '2331', 'PNB': '10666',
    'RELIANCE': '2885', 'SBICARD': '17939', 'SBILIFE': '21808', 'SRF': '3241', 'SHREECEM': '3103',
    'SIEMENS': '3145', 'SONACOMS': '251', 'STPC': '11630', 'SUNPHARMA': '3351', 'SUNTV': '13404',
    'SYNGENE': '15136', 'TATACOMM': '3426', 'TCS': '11536', 'TATACONSUM': '3432', 'TATAELXSI': '3435',
    'TATAMOTORS': '3456', 'TATAPOWER': '3440', 'TATASTEEL': '3499', 'TECHM': '13538', 'TITAN': '3506',
    'TORNTPHARM': '3540', 'TRENT': '3568', 'TVSMOTOR': '3709', 'ULTRACEMCO': '11532', 'UPL': '11287',
    'UNITDSPR': '16713', 'VBL': '17135', 'VEDL': '3063', 'VOLTAS': '3718', 'WIPRO': '3787',
    'YESBANK': '11915', 'ZEEL': '3812', 'ZOMATO': '5097'
}

# --- ४. हेल्पर्स आणि डेटा मॅनेजमेंट ---
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
    try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
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

# --- ५. स्कॅनर इंजिन ---
def scanner():
    global status_log, traded_today
    send_telegram("🚀 **NSE Algo Monitor Started!**")

    while True:
        now = datetime.now()
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
                send_telegram(f"🎯 **Signal: {name}**\nPrice: ₹{entry}\nSL: ₹{sl:.2f}\nTGT: ₹{tgt:.2f}")
                status_log.insert(0, {"time": now.strftime('%H:%M'), "stock": name, "status": f"{TRADE_SIDE} @ {entry}"})
                save_logs(status_log)
                if len(traded_today) >= MAX_TRADES: break
            time.sleep(0.6)
        time.sleep(30)

# --- ६. HTML इंटरफेस ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSE Algo Monitor</title><meta http-equiv="refresh" content="30">
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: sans-serif; text-align: center; padding: 20px; }
        .header { background: linear-gradient(135deg, #1f6feb, #238636); padding: 20px; border-radius: 12px; margin-bottom: 25px; color: white; }
        table { width: 100%; max-width: 800px; margin: auto; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; border-bottom: 1px solid #30363d; text-align: center; }
        th { background: #21262d; color: #58a6ff; }
        .BUY { color: #39d353; font-weight: bold; }
        .SELL { color: #ff7b72; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header"><h1>📊 NSE ALGO MONITOR</h1></div>
    <table>
        <thead><tr><th>Time</th><th>Stock</th><th>Signal</th></tr></thead>
        <tbody>
            {% if logs %}{% for log in logs %}
            <tr><td>{{ log.time }}</td><td>{{ log.stock }}</td><td class="{{ 'BUY' if 'BUY' in log.status else 'SELL' }}">{{ log.status }}</td></tr>
            {% endfor %}{% else %}<tr><td colspan="3" style="padding:40px;">Waiting for signals...</td></tr>{% endif %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logs=status_log)

if __name__ == "__main__":
    threading.Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
