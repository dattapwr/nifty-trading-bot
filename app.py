import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time
from flask import Flask, render_template

app = Flask(__name__)

# --- तुमची माहिती ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
REPORT_SENT = False

# सेक्टर्स आणि टॉप १० स्टॉक्स
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
    for s_code in SECTORS.keys():
        try:
            d = yf.download(s_code, period='1d', interval='15m', progress=False, threads=False)
            if not d.empty:
                change = ((d['Close'].iloc[-1] - d['Open'].iloc[0]) / d['Open'].iloc[0]) * 100
                performance.append({'code': s_code.replace('^CNX', ''), 'change': float(change), 'full_code': s_code})
        except: continue
    performance.sort(key=lambda x: x['change'], reverse=True)
    return performance[:2], performance[-2:]

def check_strategy(ticker, side):
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False, threads=False)
        if len(df) < 3: return None
        c0, c1, c2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
        is_inside = (float(c1['High']) < float(c2['High'])) and (float(c1['Low']) > float(c2['Low']))
        tm = datetime.now(IST).strftime('%H:%M:%S')
        if side == "BUY" and is_inside and (float(c0['Close']) > float(c1['High'])):
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'BUY'}
        if side == "SELL" and is_inside and (float(c0['Close']) < float(c1['Low'])):
            return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'SELL'}
    except: return None
    return None

@app.route('/')
def home():
    global REPORT_SENT
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    found_stocks, h2, l2 = [], [], []
    
    market_active = time(9, 15) <= curr_time <= time(15, 30)

    # सकाळी हिस्टरी रिसेट
    if curr_time < time(9, 10):
        SIGNAL_HISTORY.clear()
        REPORT_SENT = False

    if market_active:
        h2, l2 = get_top_sectors()
        for s_list, side in [(h2, "BUY"), (l2, "SELL")]:
            for s in s_list:
                for t in SECTORS[s['full_code']]:
                    res = check_strategy(t, side)
                    if res:
                        found_stocks.append(res)
                        # नवीन सिग्नल असल्यास हिस्ट्रीत टाकणे आणि मेसेज पाठवणे
                        if not any(x['s'] == t and x['type'] == side and x['t'][:5] == res['t'][:5] for x in SIGNAL_HISTORY):
                            SIGNAL_HISTORY.append(res)
                            icon = "🚀" if side == "BUY" else "📉"
                            send_telegram(f"{icon} *{side}:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}\n⏰ Time: {res['t']}")

    # ३:३० नंतर डेली रिपोर्ट
    if curr_time > time(15, 30) and not REPORT_SENT and SIGNAL_HISTORY:
        report_msg = "📋 *Today's Signal Report:*\n\n"
        for h in SIGNAL_HISTORY:
            report_msg += f"• {h['t'][:5]} | {h['s']} | {h['type']} @ {h['p']}\n"
        send_telegram(report_msg)
        REPORT_SENT = True

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], h2=h2, l2=l2, market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
