import yfinance as yf
import requests
import os
import pytz
from datetime import datetime, time
from flask import Flask, render_template

app = Flask(__name__)

# --- तुमची माहिती ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

LAST_ALERTS = {}

# स्टॉक्सची यादी (कमी स्टॉक्स ठेवल्यास स्कॅनिंग फास्ट होईल)
STOCKS_TO_SCAN = [
    'TATAMOTORS.NS', 'M&M.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
    'INFY.NS', 'TCS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'AXISBANK.NS', 
    'JINDALSTEL.NS', 'TATASTEEL.NS', 'SUNPHARMA.NS', 'ITC.NS'
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

def scan_stocks():
    found = []
    now_ist = datetime.now(IST)
    now_time = now_ist.time()
    
    # ९:३० ते ३:३० दरम्यान (मार्केट वेळ)
    if not (time(9, 30) <= now_time <= time(15, 30)):
        return []

    for t in STOCKS_TO_SCAN:
        try:
            # ५ मिनिटांच्या कॅन्डलचा डेटा
            df = yf.download(t, period='2d', interval='5m', progress=False)
            # डेली डेटा (कालचा High/Low साठी)
            daily = yf.download(t, period='5d', interval='1d', progress=False)
            
            if len(df) < 5 or len(daily) < 2: continue
            
            # कालचा डेटा (Daily)
            prev_high = daily['High'].iloc[-2]
            prev_low = daily['Low'].iloc[-2]
            
            # आजचा डेटा
            today_open = df['Open'].iloc[0]
            c0 = df.iloc[-1] # चालू कॅन्डल
            c1 = df.iloc[-2] # इनसाईड कॅन्डल
            c2 = df.iloc[-3] # बाहेरची कॅन्डल (Mother Candle)

            tm = now_ist.strftime('%H:%M')

            # १. BUY LOGIC: आज ओपनिंग कालच्या हायच्या वर आहे?
            if today_open > prev_high:
                # Inside Candle अटी: c1 ही c2 च्या आत आहे का?
                is_inside = (c1['High'] < c2['High']) and (c1['Low'] > c2['Low'])
                # Breakout: चालू प्राईस c1 च्या हायच्या वर गेली का?
                if is_inside and (c0['Close'] > c1['High']):
                    alert_key = f"{t}_BUY_{now_ist.hour}_{now_ist.minute//15}"
                    if alert_key not in LAST_ALERTS:
                        msg = f"🚀 *BUY ALERT!* 🚀\n\n🏢 *Stock:* `{t}`\n💰 *Price:* ₹{round(c0['Close'], 2)}\n⏰ *Time:* {tm}"
                        send_telegram(msg)
                        LAST_ALERTS[alert_key] = True
                    found.append({'s': t, 'p': round(c0['Close'], 2), 't': tm, 'type': 'BUY'})

            # २. SELL LOGIC: आज ओपनिंग कालच्या लोच्या खाली आहे?
            elif today_open < prev_low:
                is_inside = (c1['High'] < c2['High']) and (c1['Low'] > c2['Low'])
                # Breakdown: चालू प्राईस c1 च्या लोच्या खाली गेली का?
                if is_inside and (c0['Close'] < c1['Low']):
                    alert_key = f"{t}_SELL_{now_ist.hour}_{now_ist.minute//15}"
                    if alert_key not in LAST_ALERTS:
                        msg = f"📉 *SELL ALERT!* 📉\n\n🏢 *Stock:* `{t}`\n💰 *Price:* ₹{round(c0['Close'], 2)}\n⏰ *Time:* {tm}"
                        send_telegram(msg)
                        LAST_ALERTS[alert_key] = True
                    found.append({'s': t, 'p': round(c0['Close'], 2), 't': tm, 'type': 'SELL'})

        except Exception as e:
            print(f"Error scanning {t}: {e}")
            continue
    return found

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    stocks_data = scan_stocks()
    return render_template('index.html', 
                           stocks=stocks_data, 
                           date=now_ist.strftime('%d-%m-%Y'),
                           current_time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
