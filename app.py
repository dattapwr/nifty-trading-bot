import yfinance as yf
import requests
import os
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

# --- तुमचे क्रेडेंशियल्स ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# सेक्टर मॅपिंग (फक्त प्रमुख ८ सेक्टर)
SECTOR_MAP = {
    '^CNXAUTO': 'Automobile', '^CNXBANK': 'Banking', '^CNXIT': 'IT',
    '^CNXPHARMA': 'Pharma', '^CNXMETAL': 'Metals', '^CNXFMCG': 'FMCG',
    '^CNXINFRA': 'Infra', '^CNXENERGY': 'Energy'
}

# प्रत्येक सेक्टरमधील फक्त टॉप १० लिक्विड स्टॉक्स
SECTOR_STOCKS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'ASHOKLEY.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS', 'EICHERMOT.NS', 'TVSMOTOR.NS', 'BALKRISIND.NS', 'BHARATFORG.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'BANKBARODA.NS', 'PNB.NS', 'INDUSINDBK.NS', 'IDFCFIRSTB.NS', 'AUBANK.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS', 'LTIM.NS', 'COFORGE.NS', 'MPHASIS.NS', 'PERSISTENT.NS', 'LTTS.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'APOLLOHOSP.NS', 'LUPIN.NS', 'ALKEM.NS', 'TORNTPHARM.NS', 'AUROPHARMA.NS', 'GLENMARK.NS'],
    '^CNXMETAL': ['TATASTEEL.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'SAIL.NS', 'NATIONALUM.NS', 'NMDC.NS', 'HINDCOPPER.NS', 'APOLLOTYRE.NS'],
    '^CNXFMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS', 'TATACONSUM.NS', 'COLPAL.NS', 'MARICO.NS', 'GODREJCP.NS', 'UBL.NS'],
    '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'GRASIM.NS', 'CONCOR.NS', 'BHEL.NS', 'SIEMENS.NS', 'ULTRACEMCO.NS', 'DLF.NS', 'AMBUJACEM.NS'],
    '^CNXENERGY': ['ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BPCL.NS', 'IOC.NS', 'GAIL.NS', 'RELIANCE.NS', 'HINDPETRO.NS', 'TATAPOWER.NS', 'ADANIGREEN.NS']
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}"
    try: requests.get(url, timeout=5)
    except: pass

def get_worst_sector():
    """आजचा सर्वात जास्त पडलेला १ सेक्टर शोधणे"""
    performance = []
    for sym in SECTOR_MAP.keys():
        try:
            # ५०२ एरर टाळण्यासाठी फक्त १ दिवसाचा डेटा
            d = yf.download(sym, period='1d', interval='15m', progress=False)
            if not d.empty:
                chg = ((d['Close'].iloc[-1] - d['Open'].iloc[0]) / d['Open'].iloc[0]) * 100
                performance.append({'sym': sym, 'chg': chg, 'name': SECTOR_MAP[sym]})
        except: continue
    return sorted(performance, key=lambda x: x['chg'])[0] if performance else None

def scan_stocks():
    found = []
    top_down_sec = get_worst_sector()
    
    if top_down_sec:
        tickers = SECTOR_STOCKS.get(top_down_sec['sym'], [])
        for t in tickers:
            try:
                # वेगवान स्कॅनिंगसाठी कमी डेटा पॉईंट्स
                df = yf.download(t, period='2d', interval='5m', progress=False)
                d_df = yf.download(t, period='5d', interval='1d', progress=False)
                
                if df.empty or d_df.empty: continue
                
                cp = float(df['Close'].iloc[-1])
                op = float(df['Open'].iloc[0])
                pl = float(d_df['Low'].iloc[-2])

                # कंडिशन: Open <= Prev Low आणि ३ लाल कॅन्डल
                if op <= pl and cp >= 300:
                    if (df['Close'].iloc[-2] < df['Open'].iloc[-2]) and \
                       (df['Close'].iloc[-3] < df['Open'].iloc[-3]) and \
                       (df['Close'].iloc[-4] < df['Open'].iloc[-4]):
                        
                        tm = datetime.now().strftime('%H:%M')
                        found.append({'s': t, 'p': round(cp,2), 't': tm, 'sec': top_down_sec['name']})
                        send_telegram(f"🚩 Top Down Sector ({top_down_sec['name']}): {t} @ ₹{round(cp,2)} ({tm})")
            except: continue
    return found

@app.route('/')
def home():
    try:
        stocks = scan_stocks()
        return render_template('index.html', stocks=stocks)
    except Exception as e:
        return f"सर्व्हर लोड होत आहे, कृपया रिफ्रेश करा. (Error: {str(e)})"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
