import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
from flask import Flask, render_template
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स (खात्री करा की टोकन नवीन आहे) ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "YOUR_NEW_TOKEN_HERE" # <--- तुमचा नवीन टोकन इथे पेस्ट करा

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []
WATCHLIST = [
    {'symbol': 'CRUDEOIL MAR FUT', 'sid': '64115'}, 
    {'symbol': 'NATURALGAS MAR FUT', 'sid': '64132'}
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: 
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_strategy_loop():
    # सिस्टिम सुरू झाल्याचा मेसेज
    send_telegram("🚀 *Trading Bot Online!* \nChecking for Buy/Sell signals...")
    
    while True:
        try:
            now_ist = datetime.now(IST)
            today = now_ist.strftime('%Y-%m-%d')
            
            # रात्री ११:३० नंतर बोट थांबवण्यासाठी (Optional)
            if now_ist.hour >= 23 and now_ist.minute >= 30:
                pytime.sleep(300)
                continue

            for stock in WATCHLIST:
                data = None
                # --- Retry Logic: ३ वेळा प्रयत्न करेल ---
                for i in range(3):
                    try:
                        data = dhan.intraday_minute_data(
                            security_id=stock['sid'],
                            exchange_segment='MCX_FO',
                            instrument_type='FUTCOM',
                            from_date=today,
                            to_date=today
                        )
                        if data.get('status') == 'success':
                            break
                    except Exception as e:
                        print(f"Attempt {i+1} failed for {stock['symbol']}: {e}")
                        pytime.sleep(2)

                # --- सिग्नल लॉजिक ---
                if data and data.get('status') == 'success' and 'data' in data:
                    d = data['data']
                    if 'open' in d and len(d['open']) >= 2:
                        prev_o = float(d['open'][-2])
                        prev_c = float(d['close'][-2])
                        curr_c = float(d['close'][-1])
                        candle_id = d['start_Time'][-1]
                        
                        res = None
                        
                        # --- मुख्य लॉजिक (Body to Body) ---
                        if True: # ही टेस्ट कंडिशन आहे

                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'BUY'}
                        elif prev_c > prev_o and curr_c < prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'SELL'}

                        # --- टेस्टिंगसाठी (काढून टाकू शकता) ---
                        # जर तुम्हाला फक्त बोट चालतोय का हे बघायचे असेल तर खालील २ ओळी वापरा:
                        # if not res: 
                        #     res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'SCANNING'}

                        if res:
                            # डुप्लिकेट चेक
                            is_new = not any(x['s'] == res['s'] and x['id_t'] == candle_id for x in SIGNAL_HISTORY)
                            
                            if is_new:
                                res['t'] = now_ist.strftime('%H:%M:%S')
                                res['id_t'] = candle_id
                                SIGNAL_HISTORY.append(res)
                                
                                icon = "🟢" if res['type'] == "BUY" else "🔴"
                                send_telegram(f"{icon} *{res['type']} ALERT*\n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")
                                print(f"SENT: {res['s']} {res['type']}")

                pytime.sleep(2) # Rate limit टाळण्यासाठी गॅप

        except Exception as e:
            print(f"Loop Main Error: {e}")
        
        pytime.sleep(60) # दर मिनिटाला चेक करेल

# बोटला वेगळ्या थ्रेडमध्ये सुरू करा
threading.Thread(target=check_strategy_loop, daemon=True).start()

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    return f"Bot is running! Last check at: {now_ist.strftime('%H:%M:%S')}. Found {len(SIGNAL_HISTORY)} signals."

if __name__ == "__main__":
    # Render साठी अत्यंत महत्त्वाचे:
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
