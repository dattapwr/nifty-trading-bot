import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# मोजके ५ स्टॉक्स (आधी हे ५ चालवून पाहूया)
STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'SBIN.NS', 'INFY.NS', 'TCS.NS']

def get_data_and_test(start_date, end_date):
    results = []
    # yfinance साठी एंड डेट १ दिवसाने वाढवणे
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    end_str = end_dt.strftime('%Y-%m-%d')

    for ticker in STOCKS:
        try:
            # डेटा डाऊनलोड (सिम्पल पद्धत)
            df = yf.download(ticker, start=start_date, end=end_str, interval='5m', progress=False)
            
            if df.empty: continue
            
            # डेटा क्लीनिंग (Multi-index हटवणे जर असेल तर)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            for i in range(1, len(df)):
                # वेळ ९:३० नंतरची आहे का?
                curr_time = df.index[i].astimezone(IST).time()
                if curr_time < datetime.strptime("09:30", "%H:%M").time():
                    continue

                prev = df.iloc[i-1] # आधीची कॅन्डल
                curr = df.iloc[i]   # सध्याची कॅन्डल

                # स्ट्रॅटेजी: हिरवी कॅन्डल नंतर लाल कॅन्डलने हिरव्याचा 'Low' तोडणे
                is_green = float(prev['Close']) > float(prev['Open'])
                is_red = float(curr['Close']) < float(curr['Open'])
                breakout = float(curr['Close']) < float(prev['Low'])

                if is_green and is_red and breakout:
                    dt_str = df.index[i].astimezone(IST).strftime('%d-%m %H:%M')
                    results.append({
                        't': dt_str,
                        's': ticker,
                        'type': 'SELL (Downside)',
                        'p': round(float(curr['Close']), 2),
                        'l': round(float(prev['Low']), 2)
                    })
        except Exception as e:
            print(f"Error for {ticker}: {e}")
            continue
            
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = []
    if start and end:
        bt_results = get_data_and_test(start, end)
    return render_template('index.html', bt_results=bt_results)

if __name__ == "__main__":
    app.run()
