import yfinance as yf
import pandas as pd
import requests
from flask import Flask, render_template

app = Flask(_name_)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# दिवसभराचे स्टॉक्स साठवण्यासाठी मेमरी
FOUND_STOCKS_HISTORY = []

STOCK_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
    'AXISBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS', 
    'BAJFINANCE.NS', 'MARUTI.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'M&M.NS', 
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'HCLTECH.NS',
    'WIPRO.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'DLF.NS', 'TRENT.NS',
    'HAL.NS', 'BEL.NS', 'COALINDIA.NS', 'NTPC.NS', 'ITC.NS'
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: requests.get(url, timeout=10)
    except: pass

def run_scanner():
    global FOUND_STOCKS_HISTORY
    new_alerts = []
    
    for ticker in STOCK_LIST:
        try:
            df_5m = yf.download(ticker, period='2d', interval='5m', progress=False)
            df_daily = yf.download(ticker, period='2d', interval='1d', progress=False)
            
            if len(df_5m) < 10 or len(df_daily) < 2: continue

            price = df_5m['Close'].iloc[-1]
            
            # तुमची मूळ स्ट्रॅटेजी
            if price > 400 and df_daily['Open'].iloc[-1] <= df_daily['Low'].iloc[-2]:
                cond_red = (df_5m['Close'].iloc[-2] < df_5m['Open'].iloc[-2]) and \
                           (df_5m['Close'].iloc[-3] < df_5m['Open'].iloc[-3]) and \
                           (df_5m['Close'].iloc[-4] < df_5m['Open'].iloc[-4])
                
                cond_vol = df_5m['Volume'].iloc[-1] < df_5m['Volume'].iloc[-2]

                if cond_red and cond_vol:
                    stock_data = {'symbol': ticker, 'price': round(price, 2)}
                    
                    # जर हा स्टॉक आधी सापडलेला नसेल तरच मेसेज पाठवा आणि लिस्टमध्ये टाका
                    if not any(s['symbol'] == ticker for s in FOUND_STOCKS_HISTORY):
                        msg = f"🚀 नवीन संधी!\nस्टॉक: {ticker}\nकिंमत: ₹{round(price, 2)}"
                        send_telegram_msg(msg)
                        FOUND_STOCKS_HISTORY.append(stock_data)
        except: continue
    return FOUND_STOCKS_HISTORY

@app.route('/')
def home():
    all_day_stocks = run_scanner()
    return render_template('index.html', stocks=all_day_stocks)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
