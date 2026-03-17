    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

# --- तुमची माहिती ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []

SECTORS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'LTIM.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'LUPIN.NS']
}

def run_custom_backtest(start_date, end_date):
    bt_results = []
    test_stocks = []
    for tickers in SECTORS.values(): test_stocks.extend(tickers)
    
    # स्ट्रिंग डेटला datetime ऑब्जेक्टमध्ये बदलणे
    # yfinance साठी end_date एक दिवस पुढची असावी लागते जेणेकरून पूर्ण रेंज कव्हर होईल
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    end_date_str = end_dt.strftime('%Y-%m-%d')

    print(f"बॅकटेस्ट सुरू: {start_date} ते {end_date}")
    
    # डेटा डाउनलोड करणे (५ मिनिटांचा डेटा एका महिन्यातलाच मिळतो)
    data = yf.download(test_stocks, start=start_date, end=end_date_str, interval='5m', progress=False, group_by='ticker')
    
    for ticker in test_stocks:
        try:
            df = data[ticker].dropna()
            if df.empty: continue
            
            for i in range(2, len(df)):
                c0, c1, c2 = df.iloc[i], df.iloc[i-1], df.iloc[i-2]
                
                # Inside Candle Logic
                is_inside = (float(c1['High']) < float(c2['High'])) and (float(c1['Low']) > float(c2['Low']))
                
                if is_inside:
                    dt_val = df.index[i].astimezone(IST)
                    dt_str = dt_val.strftime('%d-%m %H:%M')
                    
                    # ब्रेकआउट तपासणे
                    if float(c0['Close']) > float(c1['High']):
                        bt_results.append({'t': dt_str, 's': ticker, 'type': 'BUY', 'p': round(float(c0['Close']), 2)})
                    elif float(c0['Close']) < float(c1['Low']):
                        bt_results.append({'t': dt_str, 's': ticker, 'type': 'SELL', 'p': round(float(c0['Close']), 2)})
        except Exception as e:
            print(f"Error in {ticker}: {e}")
            continue
            
    return sorted(bt_results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    bt_data = []
    if start_date and end_date:
        bt_data = run_custom_backtest(start_date, end_date)

    return render_template('index.html', bt_results=bt_data, 
                           date=now_ist.strftime('%d-%m-%Y'), 
                           time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
