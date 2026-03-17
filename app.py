import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# निफ्टी ५० मधील काही स्टॉक्स
TEST_STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'SBIN.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
               'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS', 'AXISBANK.NS']

def run_new_strategy_backtest(start_date, end_date):
    results = []
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    end_str = end_dt.strftime('%Y-%m-%d')

    for ticker in TEST_STOCKS:
        try:
            df = yf.download(ticker, start=start_date, end=end_str, interval='5m', progress=False)
            if df.empty or len(df) < 5: continue

            for i in range(2, len(df)):
                curr_time = df.index[i].astimezone(IST).time()
                
                # अट १: वेळ ९:३० नंतरची असावी
                if curr_time < datetime.strptime("09:30", "%H:%M").time():
                    continue

                prev_candle = df.iloc[i-1] # हिरवी कॅन्डल (Green)
                curr_candle = df.iloc[i]   # लाल कॅन्डल (Red - Breakout)

                # अट २: आधीची कॅन्डल हिरवी (Green) असावी
                is_green = float(prev_candle['Close']) > float(prev_candle['Open'])
                
                # अट ३: सध्याची कॅन्डल लाल (Red) असावी
                is_red = float(curr_candle['Close']) < float(curr_candle['Open'])
                
                # अट ४: लाल कॅन्डल हिरव्या कॅन्डलच्या LOW च्या खाली क्लोज व्हावी
                breakout_down = float(curr_candle['Close']) < float(prev_candle['Low'])

                if is_green and is_red and breakout_down:
                    time_str = df.index[i].astimezone(IST).strftime('%d-%m %H:%M')
                    results.append({
                        't': time_str,
                        's': ticker,
                        'type': 'SELL (Downside)',
                        'p': round(float(curr_candle['Close']), 2),
                        'signal_low': round(float(prev_candle['Low']), 2)
                    })
        except: continue
    
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = []
    if start and end:
        bt_results = run_new_strategy_backtest(start, end)
    return render_template('index.html', bt_results=bt_results)

if __name__ == "__main__":
    app.run()
