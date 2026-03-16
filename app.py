import yfinance as yf
import requests
import os
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

# --- कॉन्फिगरेशन ---
TOKEN = os.environ.get("TOKEN", "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8")
CHAT_ID = os.environ.get("CHAT_ID", "799650120")

SECTOR_MAP = {
    '^CNXAUTO': 'Automobile', '^CNXBANK': 'Banking', '^CNXIT': 'IT',
    '^CNXPHARMA': 'Pharma', '^CNXMETAL': 'Metals', '^CNXFMCG': 'FMCG',
    '^CNXINFRA': 'Infra', '^CNXENERGY': 'Energy'
}

SECTOR_STOCKS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'ASHOKLEY.NS', 'BAJAJ-AUTO.NS', 'TVSMOTOR.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'BANKBARODA.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS', 'LTIM.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'LUPIN.NS', 'AUROPHARMA.NS'],
    '^CNXMETAL': ['TATASTEEL.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'SAIL.NS'],
    '^CNXFMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS', 'TATACONSUM.NS'],
    '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'GRASIM.NS', 'ULTRACEMCO.NS', 'DLF.NS'],
    '^CNXENERGY': ['ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BPCL.NS', 'IOC.NS', 'TATAPOWER.NS']
}

def scan_stocks():
    found = []
    all_tickers = []
    for t_list in SECTOR_STOCKS.values():
        all_tickers.extend(t_list)
    
    all_tickers = list(set(all_tickers)) # युनिक स्टॉक्स

    try:
        # ५ दिवसांचा डेटा एकाच वेळी डाऊनलोड (वेगवान कामगिरीसाठी)
        data = yf.download(all_tickers, period='5d', interval='1d', progress=False)
        
        for t in all_tickers:
            try:
                cp = data['Close'][t].iloc[-1]
                pl = data['Low'][t].iloc[-2]
                op = data['Open'][t].iloc[-1]

                # कंडिशन: आजचा ओपन कालच्या लो पेक्षा खाली किंवा बरोबर
                if op <= pl and cp >= 100:
                    tm = datetime.now().strftime('%H:%M')
                    
                    # सेक्टर शोधणे
                    stock_sec = "Nifty"
                    for s_sym, t_list in SECTOR_STOCKS.items():
                        if t in t_list:
                            stock_sec = SECTOR_MAP[s_sym]
                            break
                    
                    found.append({
                        's': t, 
                        'p': round(cp, 2), 
                        't': tm, 
                        'sec': stock_sec,
                        'tv_url': f"https://in.tradingview.com/chart/?symbol=NSE:{t.replace('.NS','')}"
                    })
            except:
                continue
    except:
        pass
        
    return sorted(found, key=lambda x: x['sec'])

@app.route('/')
def home():
    try:
        stocks_data = scan_stocks()
        today = datetime.now().strftime('%d-%m-%Y')
        return render_template('index.html', stocks=stocks_data, date=today)
    except Exception as e:
        return f"रिफ्रेश करा. त्रुटी: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
