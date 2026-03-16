import yfinance as yf
import requests
import os
from datetime import datetime, time
from flask import Flask, render_template

app = Flask(__name__)

# --- तुमचे अपडेट केलेले क्रेडेंशियल्स ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# आधी पाठवलेल्या अलर्ट्सची नोंद (Repeat टाळण्यासाठी फक्त एकाच कॅन्डलवर)
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
        print("Telegram Error")

def scan_stocks():
    found = []
    now_time = datetime.now().time()
    
    # अट ६: ९:३० AM ते २:०० PM दरम्यानच स्कॅनिंग
    if not (time(9, 30) <= now_time <= time(14, 0)):
        return []

    all_tickers = []
    for t_list in SECTOR_STOCKS.values():
        all_tickers.extend(t_list)
    all_tickers = list(set(all_tickers))

    for t in all_tickers:
        try:
            # ५ मिनिटांच्या कॅन्डल आणि डेली डेटा मिळवणे
            df = yf.download(t, period='2d', interval='5m', progress=False)
            daily = yf.download(t, period='2d', interval='1d', progress=False)
            
            if df.empty or len(df) < 5: continue
            
            prev_low = daily['Low'].iloc[0] # कालचा लो
            today_open = df['Open'].iloc[0] # आजचा ओपन

            # अट १: आजचा ओपन कालच्या लो च्या खाली
            if today_open < prev_low:
                
                c0 = df.iloc[-1] # सध्याची कॅन्डल
                c1 = df.iloc[-2] # मागील कॅन्डल (ग्रीन असावी)
                c2 = df.iloc[-3] # त्याच्या आधीची (हाय-लो चेकसाठी)

                # अट २: मागील कॅन्डल ग्रीन पाहिजे
                is_green = c1['Close'] > c1['Open']
                
                # अट ३: Inside Candle (आधीच्या कॅन्डलच्या हाय-लो च्या आत) आणि कमी व्हॉल्यूम
                is_inside = (c1['High'] < c2['High']) and (c1['Low'] > c2['Low'])
                low_volume = c1['Volume'] < c2['Volume']
                
                # अट ४: सध्याच्या कॅन्डलने त्या ग्रीन कॅन्डलचा लो तोडला
                breakdown = c0['Close'] < c1['Low']

                if is_green and is_inside and low_volume and breakdown:
                    # अट ५: जितक्या वेळा घडेल तितक्या वेळा (वेळेनुसार युनिक की)
                    tm = datetime.now().strftime('%H:%M')
                    alert_id = f"{t}_{tm}" 

                    if alert_id not in LAST_ALERTS:
                        alert_msg = (
                            f"🚩 *STRATEGY ALERT!* 🚩\n\n"
                            f"🏢 *Stock:* `{t}`\n"
                            f"💰 *Price:* ₹{round(c0['Close'], 2)}\n"
                            f"✅ *Pattern:* Inside Green Candle Breakdown\n"
                            f"⏰ *Time:* {tm}\n\n"
                            f"🔗 [View Chart](https://in.tradingview.com/chart/?symbol=NSE:{t.replace('.NS','')})"
                        )
                        send_telegram(alert_msg)
                        LAST_ALERTS[alert_id] = True
                        found.append({'s': t, 'p': round(c0['Close'], 2), 't': tm})
        except:
            continue
    return found

@app.route('/')
def home():
    try:
        stocks = scan_stocks()
        return render_template('index.html', stocks=stocks, date=datetime.now().strftime('%d-%m-%Y'))
    except Exception as e:
        return f"System Running... (Error: {str(e)})"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
