import yfinance as yf
import requests
import os
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

# --- कॉन्फिगरेशन ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# एकदा मेसेज पाठवलेल्या स्टॉक्सची यादी (पुन्हा पुन्हा मेसेज टाळण्यासाठी)
SENT_MESSAGES = set()

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

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def scan_stocks():
    found = []
    all_tickers = []
    for t_list in SECTOR_STOCKS.values():
        all_tickers.extend(t_list)
    
    all_tickers = list(set(all_tickers))

    try:
        data = yf.download(all_tickers, period='5d', interval='1d', progress=False)
        
        for t in all_tickers:
            try:
                cp = data['Close'][t].iloc[-1]
                pl = data['Low'][t].iloc[-2]
                op = data['Open'][t].iloc[-1]

                # क्रायटेरिया: Open <= Prev Low
                if op <= pl and cp >= 100:
                    tm = datetime.now().strftime('%H:%M')
                    
                    stock_sec = "Nifty"
                    for s_sym, t_list in SECTOR_STOCKS.items():
                        if t in t_list:
                            stock_sec = SECTOR_MAP[s_sym]
                            break
                    
                    stock_info = {
                        's': t, 
                        'p': round(cp, 2), 
                        't': tm, 
                        'sec': stock_sec,
                        'tv_url': f"https://in.tradingview.com/chart/?symbol=NSE:{t.replace('.NS','')}"
                    }
                    found.append(stock_info)

                    # टेलिग्राम मेसेज पाठवणे (दिवसातून एकदाच एका स्टॉकसाठी)
                    msg_id = f"{t}_{datetime.now().strftime('%Y%m%d')}"
                    if msg_id not in SENT_MESSAGES:
                        alert_msg = (
                            f"🚩 *Stock Alert!*\n\n"
                            f"🏢 *Sector:* {stock_sec}\n"
                            f"📈 *Stock:* {t}\n"
                            f"💰 *Price:* ₹{round(cp, 2)}\n"
                            f"⏰ *Time:* {tm}\n\n"
                            f"🔗 [View Chart]({stock_info['tv_url']})"
                        )
                        send_telegram(alert_msg)
                        SENT_MESSAGES.add(msg_id)
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
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
