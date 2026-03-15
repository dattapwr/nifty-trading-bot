import yfinance as yf
import pandas as pd
import requests
from flask import Flask, render_template

app = Flask(_name_)

# तुमचे टेलिग्राम डिटेल्स
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# ४०० रुपयांच्या वरचे प्रमुख NSE स्टॉक्स
STOCK_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 
    'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS', 'BAJFINANCE.NS', 'MARUTI.NS', 
    'TITAN.NS', 'ASIANPAINT.NS', 'M&M.NS', 'ULTRACEMCO.NS', 'SUNPHARMA.NS', 'JSWSTEEL.NS', 
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'BAJAJ-AUTO.NS', 'BAJAJFINSV.NS', 
    'BRITANNIA.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 
    'HCLTECH.NS', 'HEROMOTOCO.NS', 'INDUSINDBK.NS', 'LTIM.NS', 'NESTLEIND.NS', 'SBILIFE.NS', 
    'TATACONSUM.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'WIPRO.NS', 'DLF.NS', 'HAVELLS.NS', 
    'PIDILITIND.NS', 'SRF.NS', 'SIEMENS.NS', 'TRENT.NS', 'TVSMOTOR.NS', 'VBL.NS', 'HAL.NS', 
    'LUPIN.NS', 'OBEROIRLTY.NS', 'POLYCAB.NS', 'TATAELXSI.NS', 'VOLTAS.NS', 'COLPAL.NS', 
    'AUBANK.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'BALKRISIND.NS', 'BEL.NS', 'CUMMINSIND.NS', 
    'ESCORTS.NS', 'GODREJCP.NS', 'INDIAMART.NS', 'IRCTC.NS', 'JINDALSTEL.NS', 'MCDOWELL-N.NS', 
    'MPHASIS.NS', 'MRF.NS', 'PAGEIND.NS', 'PERSISTENT.NS', 'RECLTD.NS', 'TATACOMM.NS'
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: requests.get(url)
    except: pass

def run_scanner():
    alerts = []
    for ticker in STOCK_LIST:
        try:
            df_5m = yf.download(ticker, period='2d', interval='5m', progress=False)
            df_daily = yf.download(ticker, period='2d', interval='1d', progress=False)
            if len(df_5m) < 10 or len(df_daily) < 2: continue

            price = df_5m['Close'].iloc[-1]
            if price > 400 and df_daily['Open'].iloc[-1] <= df_daily['Low'].iloc[-2]:
                cond_red = (df_5m['Close'].iloc[-2] < df_5m['Open'].iloc[-2]) and \
                           (df_5m['Close'].iloc[-3] < df_5m['Open'].iloc[-3]) and \
                           (df_5m['Close'].iloc[-4] < df_5m['Open'].iloc[-4])
                
                if cond_red and (df_5m['Volume'].iloc[-1] < df_5m['Volume'].iloc[-2]):
                    msg = f"✅ स्ट्रॅटेजी मॅच!\nस्टॉक: {ticker}\nकिंमत: ₹{round(price, 2)}"
                    send_telegram_msg(msg)
                    alerts.append({'symbol': ticker, 'price': round(price, 2)})
        except: continue
    return alerts

@app.route('/')
def home():
    found = run_scanner()
    return f"स्कॅनर सुरू झाला आहे. {len(found)} स्टॉक सापडले. टेलिग्राम तपासा!"

if _name_ == "_main_":
    app.run(host='0.0.0.0', port=10000)
