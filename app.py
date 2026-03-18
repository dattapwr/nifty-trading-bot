import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

# Telegram Details
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
    # सर्व सेक्टरचा डेटा एकाच वेळी मिळवणे
    sector_list = list(SECTORS.keys())
    try:
        data = yf.download(sector_list, period='1d', interval='15m', progress=False)
        for s_code in sector_list:
            if s_code in data['Close']:
                s_data = data.xs(s_code, axis=1, level=1)
                change = ((s_data['Close'].iloc[-1] - s_data['Open'].iloc[0]) / s_data['Open'].iloc[0]) * 100
                performance.append({'code': s_code, 'change': float(change)})
    except: pass
    
    performance.sort(key=lambda x: x['change'], reverse=True)
    # टॉप २ (Buy साठी) आणि बॉटम २ (Sell साठी)
    return performance[:2], performance[-2:]

def check_strategy(ticker, side):
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False)
        if len(df) < 2: return None
        
        # फक्त २ कॅन्डल तपासणे: c0 = नुकतीच पूर्ण झालेली कॅन्डल, c1 = त्याआधीची
        c0, c1 = df.iloc[-1], df.iloc[-2]
        
        c0_green = float(c0['Close']) > float(c0['Open'])
        c0_red = float(c0['Close']) < float(c0['Open'])
        c1_green = float(c1['Close']) > float(c1['Open'])
        c1_red = float(c1['Close']) < float(c1['Open'])

        tm = datetime.now(IST).strftime('%H:%M:%S')

        # BUY: १ली लाल (c1), २री हिरवी (c0) - पूर्ण होताच सिग्नल
        if side == "BUY" and c1_red and c0_green:
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'BUY'}

        # SELL: १ली हिरवी (c1), २री लाल (c0) - पूर्ण होताच सिग्नल
        if side == "SELL" and c1_green and c0_red:
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'SELL'}
                
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
        
        # मजबूत सेक्टरमध्ये फक्त BUY शोधणे
        for s in top_2:
            for t in SECTORS[s['code']]:
                res = check_strategy(t, "BUY")
                if res:
                    found_stocks.append(res)
                    if not any(x['s'] == t and x['type'] == "BUY" and x['t'][:5] == res['t'][:5] for x in SIGNAL_HISTORY):
                        SIGNAL_HISTORY.append(res)
                        send_telegram(f"🚀 *BUY:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}")

        # कमकुवत सेक्टरमध्ये फक्त SELL शोधणे
        for s in bottom_2:
            for t in SECTORS[s['code']]:
                res = check_strategy(t, "SELL")
                if res:
                    found_stocks.append(res)
                    if not any(x['s'] == t and x['type'] == "SELL" and x['t'][:5] == res['t'][:5] for x in SIGNAL_HISTORY):
                        SIGNAL_HISTORY.append(res)
                        send_telegram(f"📉 *SELL:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
