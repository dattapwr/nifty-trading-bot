import yfinance as yf
import pandas as pd
import requests
import json
import os
from flask import Flask, render_template

app = Flask(_name_)

# तुमचे टेलिग्राम डिटेल्स
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
DATA_FILE = "stocks_found.json"

# ३० प्रमुख स्टॉक्स
STOCK_LIST = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS', 'BAJFINANCE.NS', 'MARUTI.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'M&M.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'HCLTECH.NS', 'WIPRO.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'DLF.NS', 'TRENT.NS', 'HAL.NS', 'BEL.NS', 'COALINDIA.NS', 'NTPC.NS', 'ITC.NS']

def load_history():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def save_history(history):
    with open(DATA_FILE, "w") as f:
        json.dump(history, f)

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: requests.get(url, timeout=10)
    except: pass

def run_scanner():
    history = load_history()
    for ticker in STOCK_LIST:
        try:
            df_5m = yf.download(ticker, period='2d', interval='5m', progress=False)
            df_daily = yf.download(ticker, period='2d', interval='1d', progress=False)
            if len(df_5m) < 10 or len(df_daily) < 2: continue

            price = df_5m['Close'].iloc[-1].item()
            
            # स्ट्रॅटेजी: Daily Open <= Prev Low आणि ३ Red Candles
            cond_daily = df_daily['Open'].iloc[-1].item() <= df_daily['Low'].iloc[-2].item()
            cond_red = (df_5m['Close'].iloc[-2] < df_5m['Open'].iloc[-2]) and \
                       (df_5m['Close'].iloc[-3] < df_5m['Open'].iloc[-3]) and \
                       (df_5m['Close'].iloc[-4] < df_5m['Open'].iloc[-4])
            
            if price > 200 and cond_daily and cond_red:
                if not any(s['symbol'] == ticker for s in history):
                    msg = f"🚀 स्ट्रॅटेजी अलर्ट!\nस्टॉक: {ticker}\nकिंमत: ₹{round(price, 2)}"
                    send_telegram_msg(msg)
                    history.append({'symbol': ticker, 'price': round(price, 2)})
                    save_history(history)
        except: continue
    return history

def run_backtest():
    bt_results = []
    for ticker in STOCK_LIST[:10]:
        try:
            df = yf.download(ticker, period='5d', interval='5m', progress=False)
            for i in range(10, len(df)):
                # साधी बॅकटिस्ट अट (२ सलग Red Candles)
                if (df['Close'].iloc[i-1] < df['Open'].iloc[i-1]) and (df['Close'].iloc[i-2] < df['Open'].iloc[i-2]):
                    bt_results.append({
                        'ticker': ticker, 
                        'date': df.index[i].strftime('%d-%m %H:%M'), 
                        'price': round(df['Close'].iloc[i].item(), 2)
                    })
        except: continue
    return bt_results

@app.route('/')
def home():
    stocks = run_scanner()
    return render_template('index.html', stocks=stocks)

@app.route('/backtest')
def backtest_page():
    results = run_backtest()
    return render_template('backtest.html', results=results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
