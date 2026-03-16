import yfinance as yf
import pandas as pd
import requests
import json
import os
from flask import Flask, render_template, request

# Flask ॲप सेटअप
app = Flask(__name__)

# टेलिग्राम कॉन्फिगरेशन
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
DATA_FILE = "stocks_found.json"

# स्टॉक लिस्ट
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
    found_now = []
    for ticker in STOCK_LIST:
        try:
            # लाईव्ह डेटा फेच करणे
            df_5m = yf.download(ticker, period='2d', interval='5m', progress=False)
            df_daily = yf.download(ticker, period='2d', interval='1d', progress=False)
            
            if len(df_5m) < 10 or len(df_daily) < 2: continue

            price = float(df_5m['Close'].iloc[-1])
            
            # स्ट्रॅटेजी: Daily Open <= Prev Low आणि ३ Red Candles
            cond_daily = float(df_daily['Open'].iloc[-1]) <= float(df_daily['Low'].iloc[-2])
            cond_red = (df_5m['Close'].iloc[-2] < df_5m['Open'].iloc[-2]) and \
                       (df_5m['Close'].iloc[-3] < df_5m['Open'].iloc[-3]) and \
                       (df_5m['Close'].iloc[-4] < df_5m['Open'].iloc[-4])
            
            if price > 200 and cond_daily and cond_red:
                stock_data = {'symbol': ticker, 'price': round(price, 2)}
                found_now.append(stock_data)
                
                # जर स्टॉक मेमरीमध्ये नसेल तर टेलिग्राम मेसेज पाठवा
                if not any(s['symbol'] == ticker for s in history):
                    msg = f"🚀 स्ट्रॅटेजी अलर्ट!\nस्टॉक: {ticker}\nकिंमत: ₹{round(price, 2)}"
                    send_telegram_msg(msg)
                    history.append(stock_data)
                    save_history(history)
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            continue
    return history

@app.route('/')
def home():
    stocks = run_scanner()
    return render_template('index.html', stocks=stocks)

@app.route('/backtest')
def backtest_page():
    # युझरने निवडलेली तारीख घेतो (कॅलेंडरमधून)
    selected_date = request.args.get('date')
    bt_results = []
    
    if not selected_date:
        # जर तारीख निवडली नसेल, तर रिकामे पेज दाखवा
        return render_template('backtest.html', results=[])

    # निवडलेल्या तारखेसाठी बॅकटिस्ट लॉजिक
    for ticker in STOCK_LIST[:15]: # वेळ वाचवण्यासाठी टॉप १५ स्टॉक्स
        try:
            # तारीख फॉरमॅट सेट करणे
            target = pd.to_datetime(selected_date)
            start_dt = target - pd.Timedelta(days=5) # मागील लो मिळवण्यासाठी ५ दिवस मागे
            end_dt = target + pd.Timedelta(days=1)
            
            df = yf.download(ticker, start=start_dt.strftime('%Y-%m-%d'), 
                             end=end_dt.strftime('%Y-%m-%d'), interval='5m', progress=False)
            
            if df.empty: continue
            
            # फक्त निवडलेल्या दिवसाचा डेटा वेगळा करणे
            day_data = df[df.index.date == target.date()]
            
            # मागील दिवसाचा Low काढणे
            prev_days = df[df.index.date < target.date()]
            if prev_days.empty: continue
            prev_low = prev_days['Low'].min()

            if not day_data.empty:
                # ९:१५ ची ओपनिंग चेक करणे
                open_val = day_data['Open'].iloc[0]
                
                if open_val <= prev_low:
                    # ३ सलग लाल कॅन्डल शोधणे
                    for i in range(3, len(day_data)):
                        is_red = (day_data['Close'].iloc[i-1] < day_data['Open'].iloc[i-1]) and \
                                 (day_data['Close'].iloc[i-2] < day_data['Open'].iloc[i-2]) and \
                                 (day_data['Close'].iloc[i-3] < day_data['Open'].iloc[i-3])
                        
                        if is_red:
                            bt_results.append({
                                'ticker': ticker, 
                                'date': day_data.index[i].strftime('%d-%b %H:%M'), 
                                'price': round(float(day_data['Close'].iloc[i]), 2)
                            })
                            break # एका स्टॉकसाठी एका दिवसात एकच सिग्नल पकडणे
        except Exception as e:
            print(f"Error backtesting {ticker}: {e}")
            continue
            
    return render_template('backtest.html', results=bt_results)

if __name__ == "__main__":
    # Render किंवा लोकल सर्व्हरसाठी पोर्ट १००००
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
