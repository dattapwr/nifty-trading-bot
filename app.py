import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# विश्वासाह्य १० स्टॉक्स (बॅकटेस्टिंगसाठी)
TEST_STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 
               'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS', 'AXISBANK.NS']

def get_backtest_results(start_date, end_date):
    results = []
    # yfinance साठी शेवटची तारीख १ दिवसाने वाढवणे आवश्यक असते
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    end_str = end_dt.strftime('%Y-%m-%d')

    for ticker in TEST_STOCKS:
        try:
            # ५ मिनिटांचा डेटा घेताना एरर टाळण्यासाठी सुधारणा
            df = yf.download(ticker, start=start_date, end=end_str, interval='5m', progress=False)
            
            # डेटा रिकामा असल्यास पुढे जाणे
            if df.empty or len(df) < 3:
                continue

            for i in range(2, len(df)):
                # Mother, Inside आणि Breakout कॅन्डल (व्हॅल्यूज फ्लोटमध्ये रूपांतरित करणे)
                m_high = float(df['High'].iloc[i-2])
                m_low = float(df['Low'].iloc[i-2])
                i_high = float(df['High'].iloc[i-1])
                i_low = float(df['Low'].iloc[i-1])
                curr_close = float(df['Close'].iloc[i])

                # 'Inside Bar' ची अट: मागील कॅन्डल पूर्णपणे त्याच्या आधीच्या कॅन्डलच्या आत असावी
                is_inside = (i_high < m_high) and (i_low > m_low)
                
                if is_inside:
                    time_val = df.index[i].astimezone(IST).strftime('%d-%m %H:%M')
                    # Buy सिग्नल (Inside High च्या वर क्लोजिंग)
                    if curr_close > i_high:
                        results.append({'t': time_val, 's': ticker, 'type': 'BUY', 'p': round(curr_close, 2)})
                    # Sell सिग्नल (Inside Low च्या खाली क्लोजिंग)
                    elif curr_close < i_low:
                        results.append({'t': time_val, 's': ticker, 'type': 'SELL', 'p': round(curr_close, 2)})
        except:
            continue
    
    # रिझल्ट्स वेळेनुसार क्रमाने लावणे (नवीन आधी)
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = []
    
    if start and end:
        bt_results = get_backtest_results(start, end)
        
    return render_template('index.html', bt_results=bt_results)

if __name__ == "__main__":
    app.run()
