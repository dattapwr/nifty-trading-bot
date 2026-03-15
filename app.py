from flask import Flask, render_template
import yfinance as yf

app = Flask(__name__)

def get_nifty_price():
    try:
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            return f"{price:.2f}"
        return "00.00"
    except:
        return "Error"

@app.route('/')
def home():
    price = get_nifty_price()
    return render_template('index.html', price=price)

if __name__ == '__main__':
    print("सर्व्हर सुरू होत आहे... कृपया http://127.0.0.1:5000 वर जा")
    app.run(debug=True, use_reloader=False)