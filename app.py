import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'SBIN.NS', 'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS']

def get_advanced_backtest(start_date, end_date):
    results = []
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    for ticker in STOCKS:
        try:
            # ५ मिनिटांचा डेटा आणि आदल्या दिवसाचा डेटा मिळवण्यासाठी '1d' एक्स्ट्रा डाऊनलोड करणे
            df = yf.download(ticker, start=start_date, end=end_dt.strftime('%Y-%m-%d'), interval='5m', progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # कालचा क्लोजिंग रेट मिळवण्यासाठी डेली डेटा
            hist = yf.Ticker(ticker).history(start=start_date, end=end_dt.strftime('%Y-%m-%d'))

            for i in range(1, len(df)):
                # १. वेळ अट (९:३० नंतर)
                curr_dt = df.index[i].astimezone(IST)
                if curr_dt.time() < datetime.strptime("09:30", "%H:%M").time(): continue

                # २. कालच्या क्लोजिंगपेक्षा खाली असण्याची अट
                try:
                    prev_day_close = hist.loc[:curr_dt.strftime('%Y-%m-%d')].iloc[-2]['Close']
                    if float(df.iloc[i]['Close']) >= prev_day_close: continue
                except: continue

                prev = df.iloc[i-1] # हिरवी कॅन्डल
                curr = df.iloc[i]   # लाल ब्रेकआउट कॅन्डल

                # ३. स्ट्रॅटेजी अट (हिरवी नंतर लाल ब्रेकआउट)
                is_green = float(prev['Close']) > float(prev['Open'])
                is_red = float(curr['Close']) < float(curr['Open'])
                breakout = float(curr['Close']) < float(prev['Low'])

                if is_green and is_red and breakout:
                    entry = round(float(curr['Close']), 2)
                    sl = round(float(prev['High']), 2) # हिरव्या कॅन्डलचा High
                    risk = sl - entry
                    target = round(entry - (risk * 2), 2) # १:२ टार्गेट

                    results.append({
                        't': curr_dt.strftime('%d-%m %H:%M'),
                        's': ticker,
                        'p': entry,
                        'sl': sl,
                        'tgt': target,
                        'low_val': round(float(prev['Low']), 2)
                    })
        except: continue
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = get_advanced_backtest(start, end) if start and end else []
    return render_template('index.html', bt_results=bt_results)

if __name__ == "__main__":
    app.run()
