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

# पूर्ण FnO स्टॉक्सची यादी
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
    try: requests.get(url, timeout=10)
    except: pass

def run_scanner():
    history = load_history()
    found_now = []
    for ticker in FNO_LIST:
        try:
            df_5m = yf.download(ticker, period='2d', interval='5m', progress=False)
            df_daily = yf.download(ticker, period='2d', interval='1d', progress=False)
            if len(df_5m) < 10 or len(df_daily) < 2: continue

            price = float(df_5m['Close'].iloc[-1])
            avg_vol = df_daily['Volume'].iloc[-2]
            curr_vol = df_5m['Volume'].sum()

            # फिल्टर्स: ₹४००+ किंमत आणि किमान १०% व्हॉल्यूम
            if price < 400 or curr_vol < (avg_vol * 0.1): continue

            cond_daily = float(df_daily['Open'].iloc[-1]) <= float(df_daily['Low'].iloc[-2])
            cond_red = (df_5m['Close'].iloc[-2] < df_5m['Open'].iloc[-2]) and \
                       (df_5m['Close'].iloc[-3] < df_5m['Open'].iloc[-3]) and \
                       (df_5m['Close'].iloc[-4] < df_5m['Open'].iloc[-4])
            
            if cond_daily and cond_red:
                stock_data = {'symbol': ticker, 'price': round(price, 2)}
                found_now.append(stock_data)
                if not any(s['symbol'] == ticker for s in history):
                    msg = f"🚩 FnO Alert!\nStock: {ticker}\nPrice: ₹{round(price, 2)}"
                    send_telegram_msg(msg)
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
    # रेंज बॅकटिस्टसाठी निवडक २५ स्टॉक्स (सर्व १८० स्कॅन केल्यास वेळ लागेल)
    for ticker in FNO_LIST[:25]:
        try:
            df = yf.download(ticker, start=from_date, 
                             end=(pd.to_datetime(to_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d'), 
                             interval='5m', progress=False)
            if df.empty: continue

            unique_days = sorted(set(df.index.date))
            for day in unique_days:
                day_data = df[df.index.date == day]
                # मागील दिवसाचा Low काढण्यासाठी १ दिवसाचा डेली डेटा
                d_data = yf.download(ticker, end=day.strftime('%Y-%m-%d'), period='5d', interval='1d', progress=False)
                if d_data.empty or len(day_data) < 10: continue
                
                p_low = d_data['Low'].iloc[-1]
                o_price = day_data['Open'].iloc[0]

                if o_price >= 400 and o_price <= p_low:
                    for i in range(3, len(day_data)):
                        if (day_data['Close'].iloc[i-1] < day_data['Open'].iloc[i-1]) and \
                           (day_data['Close'].iloc[i-2] < day_data['Open'].iloc[i-2]) and \
                           (day_data['Close'].iloc[i-3] < day_data['Open'].iloc[i-3]):
                            
                            ent = round(float(day_data['Close'].iloc[i]), 2)
                            ext = round(float(day_data['Close'].iloc[-1]), 2)
                            pnl = round(ent - ext, 2) # Short Selling नफा
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
