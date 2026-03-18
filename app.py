import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time
from flask import Flask, render_template, request

app = Flask(__name__)

# Telegram Settings
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []

SECTORS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS', 'ASHOKLEY.NS', 'TVSMOTOR.NS', 'BALKRISIND.NS', 'BHARATFORG.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'INDUSINDBK.NS', 'BANKBARODA.NS', 'FEDERALBNK.NS', 'IDFCFIRSTB.NS', 'AUBANK.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'LTIM.NS', 'TECHM.NS', 'PERSISTENT.NS', 'COFORGE.NS', 'MPHASIS.NS', 'LTTS.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'MANKIND.NS', 'TORNTPHARM.NS', 'LUPIN.NS', 'AUROPHARMA.NS', 'ZYDUSLIFE.NS', 'IPCALAB.NS'],
    '^CNXMETAL': ['TATASTEEL.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'SAIL.NS', 'NMDC.NS', 'NATIONALUM.NS', 'APLAPOLLO.NS', 'RATNAMANI.NS'],
    '^CNXFMCG': ['ITC.NS', 'HINDUNILVR.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'VBL.NS', 'GODREJCP.NS', 'TATACONSUM.NS', 'DABUR.NS', 'COLPAL.NS', 'MARICO.NS'],
    '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'ULTRACEMCO.NS', 'GRASIM.NS', 'NTPC.NS', 'POWERGRID.NS', 'ONGC.NS', 'BHARTIARTL.NS', 'DLF.NS'],
    '^CNXENERGY': ['RELIANCE.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS', 'BPCL.NS', 'IOC.NS', 'GAIL.NS', 'ADANIGREEN.NS', 'ADANITRANS.NS', 'TATAPOWER.NS']
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.get(url, params=params, timeout=10)
    except: pass

def check_strategy(ticker):
    try:
        # ५ मिनिटांच्या कॅन्डलवर डेटा मिळवणे
        df = yf.download(ticker, period='1d', interval='5m', progress=False, threads=True)
        if len(df) < 3: return None
        
        # Yahoo Finance चा डेटा उशिरा येतो, म्हणून आपण शेवटच्या २ कॅण्डल्स तपासतो
        for i in range(-1, -3, -1):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            
            curr_green = float(curr['Close']) > float(curr['Open'])
            curr_red = float(curr['Close']) < float(curr['Open'])
            prev_green = float(prev['Close']) > float(prev['Open'])
            prev_red = float(prev['Close']) < float(prev['Open'])
            
            # कॅन्डलची वेळ (ID साठी)
            candle_time = df.index[i].astimezone(IST).strftime('%H:%M')
            display_time = datetime.now(IST).strftime('%H:%M:%S')

            # BUY: मागील लाल (c1) + आताची हिरवी (c0)
            if prev_red and curr_green:
                return {'s': ticker, 'p': round(float(curr['Close']), 2), 't': display_time, 'id_t': candle_time, 'type': 'BUY'}

            # SELL: मागील हिरवी (c1) + आताची लाल (c0)
            if prev_green and curr_red:
                return {'s': ticker, 'p': round(float(curr['Close']), 2), 't': display_time, 'id_t': candle_time, 'type': 'SELL'}
    except: return None
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    market_active = time(9, 15) <= curr_time <= time(15, 30)
    
    found_stocks = []
    if market_active:
        for sector, tickers in SECTORS.items():
            for t in tickers:
                res = check_strategy(t)
                if res:
                    found_stocks.append(res)
                    # जर हा सिग्नल त्याच वेळेसाठी इतिहासात नसेल तरच पाठवा
                    if not any(x['s'] == t and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                        SIGNAL_HISTORY.append(res)
                        icon = "🚀" if res['type'] == "BUY" else "📉"
                        send_telegram(f"{icon} *{res['type']}:* `{t}` @ ₹{res['p']}\n⏰ Time: {res['t']}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
