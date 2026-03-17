import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# बॅकटेस्टसाठी प्रमुख स्टॉक्स
TEST_STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 
               'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS', 'AXISBANK.NS']

def get_backtest_data(start_date, end_date):
    results = []
    # yfinance साठी end_date एक दिवस पुढची लागते
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    end_str = end_dt.strftime('%Y-%m-%d')

    for ticker in TEST_STOCKS:
        try:
            # ५ मिनिटांचा डेटा डाऊनलोड करणे
            df = yf.download(ticker, start=start_date, end=end_str, interval='5m', progress=False)
            
            if df.empty or len(df) < 3: continue

            for i in range(2, len(df)):
                # Mother, Inside आणि Breakout कॅन्डल ओळखणे
                c2 = df.iloc[i-2] # Mother
                c1 = df.iloc[i-1] # Inside
                c0 = df.iloc[i]   # Breakout

                # Inside Candle लॉजिक (High/Low तुलना)
                is_inside = (float(c1['High']) < float(c2['High'])) and (float(c1['Low']) > float(c2['Low']))
                
                if is_inside:
                    time_str = df.index[i].astimezone(IST).strftime('%d-%m %H:%M')
                    # Buy ब्रेकआउट
                    if float(c0['Close']) > float(c1['High']):
                        results.append({'t': time_str, 's': ticker, 'type': 'BUY', 'p': round(float(c0['Close']), 2)})
                    # Sell ब्रेकआउट
                    elif float(c0['Close']) < float(c1['Low']):
                        results.append({'t': time_str, 's': ticker, 'type': 'SELL', 'p': round(float(c0['Close']), 2)})
        except:
            continue
    
    # वेळेनुसार रिझल्ट सॉर्ट करणे
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def index():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = []
    
    if start and end:
        bt_results = get_backtest_data(start, end)
        
    return render_template('index.html', bt_results=bt_results)

if __name__ == "__main__":
    app.run(debug=True)
