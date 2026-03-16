import yfinance as yf
import requests
import os
from datetime import datetime, time
from flask import Flask, render_template

app = Flask(__name__)

# --- तुमचे क्रेडेंशियल्स ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

LAST_ALERTS = {}

SECTOR_STOCKS = {
    '^CNXAUTO': ['TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'ASHOKLEY.NS', 'BAJAJ-AUTO.NS', 'TVSMOTOR.NS'],
    '^CNXBANK': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'BANKBARODA.NS'],
    '^CNXIT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS', 'LTIM.NS'],
    '^CNXPHARMA': ['SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'LUPIN.NS', 'AUROPHARMA.NS'],
    '^CNXMETAL': ['TATASTEEL.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'SAIL.NS'],
    '^CNXFMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS', 'TATACONSUM.NS'],
    '^CNXINFRA': ['LT.NS', 'RELIANCE.NS', 'ADANIPORTS.NS', 'GRASIM.NS', 'ULTRACEMCO.NS', 'DLF.NS'],
    '^CNXENERGY': ['ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BPCL.NS', 'IOC.NS', 'TATAPOWER.NS']
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=10)
    except:
        pass

def scan_stocks():
    found = []
    now_time = datetime.now().time()
    
    # ९:३० AM ते २:०० PM दरम्यान स्कॅनिंग
    if not (time(9, 30) <= now_time <= time(14, 0)):
        return []

    all_tickers = []
    for t_list in SECTOR_STOCKS.values():
        all_tickers.extend(t_list)
    all_tickers = list(set(all_tickers))

    for t in all_tickers:
        try:
            df = yf.download(t, period='2d', interval='5m', progress=False)
            daily = yf.download(t, period='2d', interval='1d', progress=False)
            
            if df.empty or len(df) < 5: continue
            
            prev_high = daily['High'].iloc[0]
            prev_low = daily['Low'].iloc[0]
            today_open = df['Open'].iloc[0]

            c0 = df.iloc[-1] # Current Candle
            c1 = df.iloc[-2] # Potential Inside Candle
            c2 = df.iloc[-3] # Reference Candle

            tm = datetime.now().strftime('%H:%M')
            alert_id = f"{t}_{tm}"

            # --- १. बेअरिश लॉजिक (SELL) ---
            if today_open < prev_low:
                is_green = c1['Close'] > c1['Open']
                is_inside = (c1['High'] < c2['High']) and (c1['Low'] > c2['Low'])
                low_vol = c1['Volume'] < c2['Volume']
                
                if is_green and is_inside and low_vol and (c0['Low'] < c1['Low']):
                    if alert_id not in LAST_ALERTS:
                        msg = f"📉 *SELL ALERT!* 📉\n\n🏢 *Stock:* `{t}`\n💰 *Price:* ₹{round(c0['Close'], 2)}\n✅ *Pattern:* Inside Green Breakdown\n⏰ *Time:* {tm}\n\n🔗 [View Chart](https://in.tradingview.com/chart/?symbol=NSE:{t.replace('.NS','')})"
                        send_telegram(msg)
                        LAST_ALERTS[alert_id] = True
                        found.append({'s': t, 'p': round(c0['Close'], 2), 't': tm, 'type': 'SELL'})

            # --- २. बुलिश लॉजिक (BUY) ---
            elif today_open > prev_high:
                is_red = c1['Close'] < c1['Open']
                is_inside = (c1['High'] < c2['High']) and (c1['Low'] > c2['Low'])
                low_vol = c1['Volume'] < c2['Volume']
                
                if is_red and is_inside and low_vol and (c0['High'] > c1['High']):
                    if alert_id not in LAST_ALERTS:
                        msg = f"🚀 *BUY ALERT!* 🚀\n\n🏢 *Stock:* `{t}`\n💰 *Price:* ₹{round(c0['Close'], 2)}\n✅ *Pattern:* Inside Red Breakout\n⏰ *Time:* {tm}\n\n🔗 [View Chart](https://in.tradingview.com/chart/?symbol=NSE:{t.replace('.NS','')})"
                        send_telegram(msg)
                        LAST_ALERTS[alert_id] = True
                        found.append({'s': t, 'p': round(c0['Close'], 2), 't': tm, 'type': 'BUY'})
        except:
            continue
    return found

@app.route('/')
def home():
    stocks_data = scan_stocks()
    return render_template('index.html', stocks=stocks_data, date=datetime.now().strftime('%d-%m-%Y'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
