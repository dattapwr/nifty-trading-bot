import yfinance as yf
from flask import Flask, render_template
import os
from datetime import datetime
import pytz

app = Flask(__name__)

# IST Timezone setup
IST = pytz.timezone('Asia/Kolkata')

@app.route('/')
def home():
    try:
        now = datetime.now(IST)
        # फक्त एक स्टॉक टेस्टसाठी घेऊ जेणेकरून एरर समजेल
        ticker = "TATAMOTORS.NS"
        data = yf.download(ticker, period='1d', interval='5m', progress=False)
        
        price = "Data Error"
        if not data.empty:
            price = round(float(data['Close'].iloc[-1]), 2)

        return f"<h1>Scanner Active!</h1><p>Stock: {ticker} | Price: {price} | Time: {now.strftime('%H:%M:%S')}</p>"
    except Exception as e:
        return f"Error details: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
