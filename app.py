import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# बॅकटेस्टिंगसाठी प्रमुख स्टॉक्स
STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'SBIN.NS', 'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS', 'ICICIBANK.NS', 'HDFCBANK.NS']

def get_filtered_backtest(start_date, end_date):
    results = []
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    for ticker in STOCKS:
        try:
            # १. इंट्राडे डेटा (५ मिनिटे)
            df = yf.download(ticker, start=start_date, end=end_dt.strftime('%Y-%m-%d'), interval='5m', progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # २. डेली डेटा (कालचा क्लोज शोधण्यासाठी)
            daily = yf.download(ticker, start=start_date, end=end_dt.strftime('%Y-%m-%d'), interval='1d', progress=False)

            for i in range(1, len(df)):
                curr_dt = df.index[i].astimezone(IST)
                # ९:३० नंतरचे सिग्नल्स पाहणे
                if curr_dt.time() < datetime.strptime("09:30", "%H:%M").time(): continue

                # --- अट: स्टॉक कालच्या क्लोजिंग पेक्षा खाली पाहिजे ---
                try:
                    today_str = curr_dt.strftime('%Y-%m-%d')
                    prev_close = daily.loc[:today_str].iloc[-2]['Close']
                    if float(df.iloc[i]['Close']) >= prev_close: continue
                except: continue

                # ३. स्ट्रॅटेजी: ग्रीन कॅन्डल लो ब्रेकआऊट
                prev = df.iloc[i-1] 
                curr = df.iloc[i]   

                is_green = float(prev['Close']) > float(prev['Open'])
                is_red = float(curr['Close']) < float(curr['Open'])
                breakout = float(curr['Close']) < float(prev['Low'])

                if is_green and is_red and breakout:
                    entry = round(float(curr['Close']), 2)
                    sl = round(float(prev['High']), 2) # हिरव्या कॅन्डलचा हाय (SL)
                    risk = sl - entry
                    target = round(entry - (risk * 2), 2) # १:२ टार्गेट

                    results.append({
                        't': curr_dt.strftime('%d-%m %H:%M'),
                        's': ticker,
                        'p': entry,
                        'sl': sl,
                        'tgt': target
                    })
        except: continue
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = get_filtered_backtest(start, end) if start and end else []
    return render_template('index.html', bt_results=bt_results)

if __name__ == "__main__":
    app.run()
