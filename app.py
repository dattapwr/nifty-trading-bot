import os
import requests
from flask import Flask, render_template
from dhanhq import dhanhq
from datetime import datetime

app = Flask(__name__)

# --- तुमची माहिती भरा ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "तुमचा_टोकन_इथे_टाका" # रोज सकाळी एकदा बदला
TELEGRAM_BOT_TOKEN = "7963920630:AAH..." # तुमच्या बॉटचा टोकन
TELEGRAM_CHAT_ID = "तुमचा_चॅट_आयडी" 

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
last_signal_time = None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}"
    requests.get(url)

@app.route('/')
def monitor():
    global last_signal_time
    try:
        # Crude Oil March Fut चा डेटा (Security ID: 420844)
        # टीप: जर आयडी बदलला असेल तर धनच्या 'Security Master' मधून नवीन घ्यावा लागेल
        resp = dhan.historical_minute_charts(420844, 'MCX', 'INTRA')
        
        if resp and 'data' in resp:
            candles = resp['data']
            if len(candles) >= 2:
                prev = candles[-2] # लाल कँडल
                curr = candles[-1] # हिरवी कँडल
                
                # १. पहिली लाल (Open > Close)
                # २. दुसरी हिरवी (Close > Open)
                # ३. अट: हिरव्याची बॉडी लालच्या वर (Close > Prev Open)
                if prev['open'] > prev['close'] and curr['close'] > curr['open']:
                    if curr['close'] > prev['open']:
                        now = datetime.now().strftime("%H:%M")
                        
                        # एकाच कँडलवर वारंवार मेसेज जाऊ नये म्हणून
                        if last_signal_time != now:
                            msg = f"🚀 CRUDE OIL ALERT!\n\nBuy Above: {curr['close']}\nTime: {now}\nPattern: Body Breakout ✅"
                            send_telegram(msg)
                            last_signal_time = now
                            return render_template('index.html', signal="BUY", price=curr['close'], time=now)

        return render_template('index.html', signal="WAITING", price="Scanning...", time="Live")
    
    except Exception as e:
        return f"कनेक्शन एरर: {str(e)}. कृपया टोकन तपासा."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
