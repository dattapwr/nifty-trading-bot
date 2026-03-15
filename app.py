import yfinance as yf
import pandas as pd
import requests
import json
import os
from flask import Flask, render_template

app = Flask(_name_)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
DATA_FILE = "stocks_found.json"

# ३० प्रमुख स्टॉक्सची लिस्ट
STOCK_LIST = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS', 'BAJFINANCE.NS', 'MARUTI.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'M&M.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'HCLTECH.NS', 'WIPRO.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'DLF.NS', 'TRENT.NS', 'HAL.NS', 'BEL.NS', 'COALINDIA.NS', 'NTPC.NS', 'ITC.NS']

def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
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

            price = df_5m['Close'].iloc[-1]
            # तुमची अट तपासा
            if price > 200 and df_daily['Open'].iloc[-1] <= df_daily['Low'].iloc[-2]:
                cond_red = (df_5m['Close'].iloc[-2] < df_5m['Open'].iloc[-2]) and \
                           (df_5m['Close'].iloc[-3] < df_5m['Open'].iloc[-3]) and \
                           (df_5m['Close'].iloc[-4] < df_5m['Open'].iloc[-4])
                
                if cond_red and not any(s['symbol'] == ticker for s in history):
                    msg = f"🚀 नवीन स्टॉक सापडला!\nस्टॉक: {ticker}\nकिंमत: ₹{round(price, 2)}"
                    send_telegram_msg(msg)
                    history.append({'symbol': ticker, 'price': round(price, 2)})
                    save_history(history)
        except: continue
    return history

@app.route('/')
def home():
    stocks = run_scanner()
    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
