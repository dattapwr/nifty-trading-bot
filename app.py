import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# निफ्टी ५० मधील टॉप २० स्टॉक्स
STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'SBIN.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
          'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS', 'AXISBANK.NS', 'M&M.NS', 'BAJAJ-AUTO.NS',
          'BHARTIARTL.NS', 'KOTAKBANK.NS', 'ASIANPAINT.NS', 'TITAN.NS', 'MARUTI.NS', 'SUNPHARMA.NS']

def run_price_action_backtest(start_date, end_date):
    results = []
    # yfinance साठी एंड डेट १ दिवसाने वाढवणे
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    end_str = end_dt.strftime('%Y-%m-%d')

    for ticker in STOCKS:
        try:
            df = yf.download(ticker, start=start_date, end=end_str, interval='5m', progress=False)
            if df.empty or len(df) < 10: continue

            for i in range(5, len(df)):
                # १. वेळ तपासणे (९:३० नंतर)
                curr_time = df.index[i].astimezone(IST).time()
                if curr_time < datetime.strptime("09:30", "%H:%M").time():
                    continue

                prev_5 = df.iloc[i-5:i] # मागील ५ कॅन्डल
                green_candle = df.iloc[i-1] # हिरवी कॅन्डल (जिचा Low आपल्याला पाहायचा आहे)
                red_candle = df.iloc[i]   # सध्याची लाल कॅन्डल (Breakout)

                # अट १: डाउन ट्रेंड (मागील ५ पैकी ३ कॅन्डल लाल असाव्यात)
                down_trend = (prev_5['Close'] < prev_5['Open']).sum() >= 3
                
                # अट २: मागील कॅन्डल हिरवी (Green) असावी
                is_green = green_candle['Close'] > green_candle['Open']
                
                # अट ३: सध्याची कॅन्डल लाल (Red) असावी आणि हिरव्या कॅन्डलच्या Low च्या खाली क्लोज व्हावी
                is_red = red_candle['Close'] < red_candle['Open']
                breakout_down = red_candle['Close'] < green_candle['Low']

                if down_trend and is_green and is_red and breakout_down:
                    time_val = df.index[i].astimezone(IST).strftime('%d-%m %H:%M')
                    results.append({
                        't': time_val,
                        's': ticker,
                        'type': 'SELL (Downside)',
                        'p': round(float(red_candle['Close']), 2),
                        'low': round(float(green_candle['Low']), 2)
                    })
        except: continue
    
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = []
    if start and end:
        bt_results = run_price_action_backtest(start, end)
    return render_template('index.html', bt_results=bt_results)

if __name__ == "__main__":
    app.run()
