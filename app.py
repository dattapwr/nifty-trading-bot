import yfinance as yf
import requests
import os
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

# --- कॉन्फिगरेशन ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# NSE सेक्टर इंडेक्सची यादी
SECTOR_INDEXES = [
    '^CNXAUTO', '^CNXBANK', '^CNXIT', '^CNXPHARMA', 
    '^CNXMETAL', '^CNXFMCG', '^CNXINFRA', '^CNXENERGY'
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: requests.get(url, timeout=5)
    except: pass

def get_live_sector_data():
    """सर्वात जास्त पडलेले ३ सेक्टर शोधणे"""
    sector_results = []
    for sector in SECTOR_INDEXES:
        try:
            data = yf.download(sector, period='1d', interval='5m', progress=False)
            if not data.empty:
                # आजची टक्केवारी काढणे
                change = ((data['Close'].iloc[-1] - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
                sector_results.append({'symbol': sector, 'change': change})
        except: continue
    
    # सर्वात जास्त Negative Change असलेले ३ सेक्टर
    return sorted(sector_results, key=lambda x: x['change'])[:3]

def get_stocks_from_sector(sector_code):
    """सेक्टरनुसार NSE मधील प्रमुख स्टॉक यादी (Auto-Mapping)"""
    mapping = {
        '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'ASHOKLEY.NS'],
        '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS'],
        '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS'],
        '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'LUPIN.NS'],
        '^CNXMETAL': ['TATASTEEL.NS', 'HINDALCO.NS', 'JINDALSTEL.NS', 'JSWSTEEL.NS'],
        '^CNXFMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS'],
        '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'BHEL.NS'],
        '^CNXENERGY': ['ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BPCL.NS']
    }
    return mapping.get(sector_code, [])

def scan_logic():
    found_stocks = []
    top_down_sectors = get_live_sector_data()
    
    for sector in top_down_sectors:
        tickers = get_stocks_from_sector(sector['symbol'])
        for ticker in tickers:
            try:
                # ५ मिनिटांचा आणि डेली डेटा मागवणे
                df = yf.download(ticker, period='2d', interval='5m', progress=False)
                d_df = yf.download(ticker, period='5d', interval='1d', progress=False)
                
                if df.empty or d_df.empty: continue
                
                price = float(df['Close'].iloc[-1])
                o_price = float(df['Open'].iloc[0])
                p_low = float(d_df['Low'].iloc[-2])

                # स्ट्रॅटेजी: Open <= Prev Low आणि मागील ३ लाल कॅन्डल
                if o_price <= p_low and price >= 400:
                    if (df['Close'].iloc[-2] < df['Open'].iloc[-2]) and \
                       (df['Close'].iloc[-3] < df['Open'].iloc[-3]) and \
                       (df['Close'].iloc[-4] < df['Open'].iloc[-4]):
                        
                        time_now = datetime.now().strftime('%H:%M')
                        found_stocks.append({
                            'symbol': ticker, 
                            'price': round(price, 2), 
                            'time': time_now,
                            'sector': sector['symbol'].replace('^', '')
                        })
                        send_telegram_msg(f"🚩 Alert: {ticker} ({sector['symbol']})\nPrice: ₹{round(price,2)}\nTime: {time_now}")
            except: continue
    return found_stocks

@app.route('/')
def home():
    # NSE मधून सेक्टर स्कॅन करून रिझल्ट दाखवणे
    stocks = scan_logic()
    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
