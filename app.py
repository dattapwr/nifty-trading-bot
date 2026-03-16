import yfinance as yf
import pandas as pd
import requests
import json
import os
import time
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
DATA_FILE = "stocks_found.json"

FNO_LIST = [
    'AARTIIND.NS', 'ABB.NS', 'ABBOTINDIA.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'ALKEM.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'APOLLOTYRE.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'ATUL.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BALKRISIND.NS', 'BALRAMCHIN.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BATAINDIA.NS', 'BEL.NS', 'BERGEPAINT.NS', 'BHARATFORG.NS', 'BHARTIARTL.NS', 'BHEL.NS', 'BIOCON.NS', 'BSOFT.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CANFINHOME.NS', 'CHAMBLFERT.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'CUB.NS', 'CUMMINSIND.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLENMARK.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HAVELLS.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFC.NS', 'IDFCFIRSTB.NS', 'IEX.NS', 'IGL.NS', 'INDHOTEL.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDIGO.NS', 'INDUSINDBK.NS', 'INDUSTOWER.NS', 'INFY.NS', 'IOC.NS', 'IPCALAB.NS', 'IRCTC.NS', 'ITC.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'JSWSTEEL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'L&TFH.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LUPIN.NS', 'M&M.NS', 'M&MFIN.NS', 'MANAPPURAM.NS', 'MARICO.NS', 'MARUTI.NS', 'MCDOWELL-N.NS', 'MCX.NS', 'METROPOLIS.NS', 'MFSL.NS', 'MGL.NS', 'MOTHERSON.NS', 'MPHASIS.NS', 'MRF.NS', 'MUTHOOTFIN.NS', 'NATIONALUM.NS', 'NAVINFLUOR.NS', 'NESTLEIND.NS', 'NMDC.NS', 'NTPC.NS', 'OBEROIRLTY.NS', 'OFSS.NS', 'ONGC.NS', 'PAGEIND.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PFC.NS', 'PIDILITIND.NS', 'PIIND.NS', 'PNB.NS', 'POLYCAB.NS', 'POWERGRID.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'RECPY.NS', 'RELIANCE.NS', 'SAIL.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SRF.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TVSMOTOR.NS', 'UBL.NS', 'ULTRACEMCO.NS', 'UPL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'ZEEL.NS', 'ZYDUSLIFE.NS'
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
    try: requests.get(url, timeout=3)
    except: pass

def run_scanner():
    history = load_history()
    today_str = datetime.now().strftime('%Y-%m-%d')
    if history and history[0].get('date') != today_str:
        history = []
        save_history([])

    # ५०२ एरर टाळण्यासाठी फक्त ३०-३० स्टॉकचे तुकडे करून स्कॅन करा
    for ticker in FNO_LIST:
        try:
            # वेगवान स्कॅनिंगसाठी फक्त १ दिवसाचा ५ मिनिटांचा डेटा
            df = yf.download(ticker, period='2d', interval='5m', progress=False)
            if len(df) < 10: continue

            price = float(df['Close'].iloc[-1])
            o_price = float(df['Open'].iloc[0])
            
            # मागील दिवसाचा 'Low' मिळवण्यासाठी
            d_df = yf.download(ticker, period='5d', interval='1d', progress=False)
            p_low = float(d_df['Low'].iloc[-2])

            if o_price <= p_low and price >= 400:
                # ३ लाल कॅन्डलची अट
                if (df['Close'].iloc[-2] < df['Open'].iloc[-2]) and \
                   (df['Close'].iloc[-3] < df['Open'].iloc[-3]) and \
                   (df['Close'].iloc[-4] < df['Open'].iloc[-4]):
                    
                    if not any(s['symbol'] == ticker for s in history):
                        now_t = datetime.now().strftime('%H:%M')
                        history.append({'symbol': ticker, 'price': price, 'time': now_t, 'date': today_str})
                        save_history(history)
                        send_telegram_msg(f"🚩 Alert: {ticker} @ ₹{price} ({now_t})")
        except: continue
    return sorted(history, key=lambda x: x['time'], reverse=True)

@app.route('/')
def home():
    stocks = run_scanner()
    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
