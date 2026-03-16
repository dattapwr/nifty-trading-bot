import yfinance as yf
import pandas as pd
import requests
import json
import os
from flask import Flask, render_template, request

app = Flask(__name__)

# --- कॉन्फिगरेशन ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
DATA_FILE = "stocks_found.json"

# पूर्ण FnO यादी
FNO_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS', 
    'BAJFINANCE.NS', 'MARUTI.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'M&M.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 
    'HCLTECH.NS', 'WIPRO.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'DLF.NS', 'TRENT.NS', 'HAL.NS', 'BEL.NS', 'COALINDIA.NS', 'NTPC.NS', 'ITC.NS',
    'AARTIIND.NS', 'ABB.NS', 'ABBOTINDIA.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'ACC.NS', 'ALKEM.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'APOLLOTYRE.NS'
]

def load_history():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_history(history):
    with open(DATA_FILE, "w") as f: json.dump(history, f)

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: requests.get(url, timeout=5)
    except: pass

def run_scanner():
    history = load_history()
    found_now = []
    # स्कॅनिंगसाठी टॉप ३० स्टॉक्स (लोड कमी करण्यासाठी)
    for ticker in FNO_LIST[:30]:
        try:
            df_5m = yf.download(ticker, period='2d', interval='5m', progress=False)
            df_daily = yf.download(ticker, period='2d', interval='1d', progress=False)
            if len(df_5m) < 10 or len(df_daily) < 2: continue

            price = float(df_5m['Close'].iloc[-1])
            if price < 400: continue

            cond_daily = float(df_daily['Open'].iloc[-1]) <= float(df_daily['Low'].iloc[-2])
            cond_red = (df_5m['Close'].iloc[-2] < df_5m['Open'].iloc[-2]) and \
                       (df_5m['Close'].iloc[-3] < df_5m['Open'].iloc[-3]) and \
                       (df_5m['Close'].iloc[-4] < df_5m['Open'].iloc[-4])
            
            if cond_daily and cond_red:
                stock_data = {'symbol': ticker, 'price': round(price, 2)}
                found_now.append(stock_data)
                if not any(s['symbol'] == ticker for s in history):
                    send_telegram_msg(f"🚩 FnO Alert!\nStock: {ticker}\nPrice: ₹{round(price, 2)}")
                    history.append(stock_data)
                    save_history(history)
        except: continue
    return found_now

@app.route('/')
def home():
    stocks = run_scanner()
    return render_template('index.html', stocks=stocks)

@app.route('/backtest')
def backtest_page():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    if not from_date or not to_date:
        return render_template('backtest.html', results=[], total_pnl=0)

    bt_results = []
    total_pnl = 0
    # बॅकटिस्टसाठी फक्त २० महत्त्वाचे स्टॉक्स (502 Error टाळण्यासाठी)
    for ticker in FNO_LIST[:20]:
        try:
            df = yf.download(ticker, start=from_date, end=(pd.to_datetime(to_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d'), interval='5m', progress=False)
            if df.empty: continue

            unique_days = sorted(set(df.index.date))
            for day in unique_days:
                day_data = df[df.index.date == day]
                # Daily data download simplified
                d_df = yf.download(ticker, start=(pd.to_datetime(day) - pd.Timedelta(days=5)).strftime('%Y-%m-%d'), end=day.strftime('%Y-%m-%d'), interval='1d', progress=False)
                if d_df.empty or len(day_data) < 10: continue
                
                p_low = d_df['Low'].iloc[-1]
                o_price = day_data['Open'].iloc[0]

                if o_price >= 400 and o_price <= p_low:
                    for i in range(3, len(day_data)):
                        if (day_data['Close'].iloc[i-1] < day_data['Open'].iloc[i-1]) and \
                           (day_data['Close'].iloc[i-2] < day_data['Open'].iloc[i-2]) and \
                           (day_data['Close'].iloc[i-3] < day_data['Open'].iloc[i-3]):
                            
                            ent = round(float(day_data['Close'].iloc[i]), 2)
                            ext = round(float(day_data['Close'].iloc[-1]), 2)
                            pnl = round(ent - ext, 2)
                            total_pnl += pnl

                            bt_results.append({
                                'ticker': ticker, 'date': day.strftime('%d-%m-%Y'),
                                'time': day_data.index[i].strftime('%H:%M'),
                                'entry': ent, 'exit': ext, 'pnl': pnl
                            })
                            break
        except: continue

    return render_template('backtest.html', results=bt_results, total_pnl=round(total_pnl, 2))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
