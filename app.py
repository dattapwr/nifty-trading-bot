import yfinance as yf
import requests
import os
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

# --- कॉन्फिगरेशन (Environment Variables वापरा किंवा इथे बदला) ---
TOKEN = os.environ.get("TOKEN", "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8")
CHAT_ID = os.environ.get("CHAT_ID", "799650120")

SECTOR_MAP = {
    '^CNXAUTO': 'Automobile', '^CNXBANK': 'Banking', '^CNXIT': 'IT',
    '^CNXPHARMA': 'Pharma', '^CNXMETAL': 'Metals', '^CNXFMCG': 'FMCG',
    '^CNXINFRA': 'Infra', '^CNXENERGY': 'Energy'
}

SECTOR_STOCKS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'ASHOKLEY.NS', 'BAJAJ-AUTO.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'LUPIN.NS'],
    '^CNXMETAL': ['TATASTEEL.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS'],
    '^CNXFMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS'],
    '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'GRASIM.NS', 'ULTRACEMCO.NS'],
    '^CNXENERGY': ['ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BPCL.NS', 'IOC.NS']
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.get(url, params=params, timeout=5)
    except:
        print("Telegram Error")

def get_worst_sector():
    try:
        symbols = list(SECTOR_MAP.keys())
        # सर्व सेक्टरचा डेटा एकाच वेळी घेतोय
        data = yf.download(symbols, period='1d', interval='15m', progress=False)['Close']
        perf = []
        for sym in symbols:
            if sym in data:
                chg = ((data[sym].iloc[-1] - data[sym].iloc[0]) / data[sym].iloc[0]) * 100
                perf.append({'sym': sym, 'chg': chg, 'name': SECTOR_MAP[sym]})
        return sorted(perf, key=lambda x: x['chg'])[0] if perf else None
    except:
        return None

def scan_stocks():
    found = []
    top_down_sec = get_worst_sector()
    
    if top_down_sec:
        tickers = SECTOR_STOCKS.get(top_down_sec['sym'], [])
        # वेग वाढवण्यासाठी ५ दिवसांचा डेटा एकाच वेळी
        data = yf.download(tickers, period='5d', interval='1d', progress=False)
        
        for t in tickers:
            try:
                # क्लोज आणि प्रिव्हियस लो चेक करणे
                cp = data['Close'][t].iloc[-1]
                pl = data['Low'][t].iloc[-2]
                op = data['Open'][t].iloc[-1]

                if op <= pl and cp >= 200:
                    tm = datetime.now().strftime('%H:%M')
                    found.append({'s': t, 'p': round(cp, 2), 't': tm, 'sec': top_down_sec['name']})
                    # टेलिग्राम अलर्ट (ऑप्शनल)
                    # send_telegram(f"🚩 Alert: {t} @ ₹{round(cp,2)}")
            except:
                continue
    return found

@app.route('/')
def home():
    try:
        stocks = scan_stocks()
        return render_template('index.html', stocks=stocks)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
