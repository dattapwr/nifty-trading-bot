import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
REPORT_SENT = False

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
        
        # c0 = सध्याची कॅन्डल, c1 = मागील कॅन्डल, c2 = त्याच्या मागील कॅन्डल
        c0, c1, c2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
        
        # कॅन्डलचे रंग ठरवणे (Close > Open म्हणजे हिरवी, Close < Open म्हणजे लाल)
        c2_is_red = float(c2['Close']) < float(c2['Open'])
        c2_is_green = float(c2['Close']) > float(c2['Open'])
        
        c1_is_green = float(c1['Close']) > float(c1['Open'])
        c1_is_red = float(c1['Close']) < float(c1['Open'])

        tm = datetime.now(IST).strftime('%H:%M:%S')

        # BUY अट: १ली लाल (c2), २री हिरवी (c1) आणि सध्याची (c0) हिरव्याचा High तोडते
        if side == "BUY":
            if c2_is_red and c1_is_green:
                if float(c0['Close']) > float(c1['High']):
                    return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'BUY'}

        # SELL अट: १ली हिरवी (c2), २री लाल (c1) आणि सध्याची (c0) लालचा Low तोडते
        if side == "SELL":
            if c2_is_green and c1_is_red:
                if float(c0['Close']) < float(c1['Low']):
                    return {'s': ticker, 'p': round(float(c0['Close']), 2), 't': tm, 'type': 'SELL'}
                    
    except: return None
    return None

def run_backtest(days=7):
    results = []
    for s_code, tickers in SECTORS.items():
        for t in tickers[:3]: 
            try:
                df = yf.download(t, period=f'{days}d', interval='5m', progress=False, threads=False)
                for i in range(2, len(df)):
                    c0, c1, c2 = df.iloc[i], df.iloc[i-1], df.iloc[i-2]
                    
                    c2_red = float(c2['Close']) < float(c2['Open'])
                    c2_green = float(c2['Close']) > float(c2['Open'])
                    c1_green = float(c1['Close']) > float(c1['Open'])
                    c1_red = float(c1['Close']) < float(c1['Open'])

                    time_str = df.index[i].astimezone(IST).strftime('%d-%m %H:%M')

                    # BUY logic
                    if c2_red and c1_green and float(c0['Close']) > float(c1['High']):
                        results.append({'t': time_str, 's': t, 'type': 'BUY', 'p': round(float(c0['Close']), 2)})
                    # SELL logic
                    elif c2_green and c1_red and float(c0['Close']) < float(c1['Low']):
                        results.append({'t': time_str, 's': t, 'type': 'SELL', 'p': round(float(c0['Close']), 2)})
            except: continue
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    global REPORT_SENT
    now_ist = datetime.now(IST)
    curr_time = now_ist.time()
    
    show_bt = request.args.get('bt')
    bt_results = run_backtest() if show_bt else []

    found_stocks, h2, l2 = [], [], []
    market_active = time(9, 15) <= curr_time <= time(15, 30)

    if market_active:
        h2, l2 = get_top_sectors()
        for s_list, side in [(h2, "BUY"), (l2, "SELL")]:
            for s in s_list:
                for t in SECTORS[s['full_code']]:
                    res = check_strategy(t, side)
                    if res:
                        found_stocks.append(res)
                        if not any(x['s'] == t and x['type'] == side and x['t'][:5] == res['t'][:5] for x in SIGNAL_HISTORY):
                            SIGNAL_HISTORY.append(res)
                            send_telegram(f"{'🚀' if side=='BUY' else '📉'} *{side}:* `{t}` @ ₹{res['p']}\n📊 Sector: {s['code']}")

    return render_template('index.html', stocks=found_stocks, history=SIGNAL_HISTORY[::-1], 
                           bt_results=bt_results, market_open=market_active,
                           date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
