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

def get_top_sectors():
    performance = []
    sector_list = list(SECTORS.keys())
    try:
        # सर्व सेक्टरचा १५ मिनिटांचा डेटा मिळवून परफॉर्मन्स तपासणे
        data = yf.download(sector_list, period='1d', interval='15m', progress=False)
        for s_code in sector_list:
            if s_code in data['Close']:
                s_data = data.xs(s_code, axis=1, level=1)
                change = ((s_data['Close'].iloc[-1] - s_data['Open'].iloc[0]) / s_data['Open'].iloc[0]) * 100
                performance.append({'code': s_code, 'change': float(change)})
    except: pass
    
    performance.sort(key=lambda x: x['change'], reverse=True)
    return performance[:2], performance[-2:] # टॉप २ मजबूत आणि २ कमकुवत

def check_strategy(ticker, side):
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False, threads=True)
        if len(df) < 2: return None
        
        # मागील २ कॅण्डल्सची अट (१ली लाल, २री हिरवी किंवा उलट)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        curr_green = float(curr['Close']) > float(curr['Open'])
        curr_red = float(curr['Close']) < float(curr['Open'])
        prev_green = float(prev['Close']) > float(prev['Open'])
        prev_red = float(prev['Close']) < float(prev['Open'])
        
        candle_id = df.index[-1].astimezone(IST).strftime('%H:%M')
        display_time = datetime.now(IST).strftime('%H:%M:%S')

        # BUY: मागील लाल + आताची हिरवी
        if side == "BUY" and prev_red and curr_green:
            return {'s': ticker, 'p': round(float(curr['Close']), 2), 't': display_time, 'id_t': candle_id, 'type': 'BUY'}

        # SELL: मागील हिरवी + आताची लाल
        if side == "SELL" and prev_green and curr_red:
            return {'s': ticker, 'p': round(float(curr['Close']), 2), 't': display_time, 'id_t': candle_id, 'type': 'SELL'}
    except: return None
    return None

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    market_active = time(9, 15) <= curr_time <= time(15, 30)
    
    found_stocks = []
    if market_active:
        top_2, bottom_2 = get_top_sectors()
        
        # टॉप २ सेक्टर्समध्ये फक्त BUY ट्रेड्स शोधणे
        for s in top_2:
            for t in SECTORS[s['code']]:
                res = check_strategy(t, "BUY")
                if res:
                    found_stocks.append(res)
                    if not any(x['s'] == t and x['type'] == "BUY" and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                        SIGNAL_HISTORY.append(res)
                        send_telegram(f"🚀 *BUY:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}")

        # बॉटम २ सेक्टर्समध्ये फक्त SELL ट्रेड्स शोधणे
        for s in bottom_2:
            for t in SECTORS[s['code']]:
                res = check_strategy(t, "SELL")
                if res:
                    found_stocks.append(res)
                    if not any(x['s'] == t and x['type'] == "SELL" and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                        SIGNAL_HISTORY.append(res)
                        send_telegram(f"📉 *SELL:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
