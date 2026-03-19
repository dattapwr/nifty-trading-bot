import os
import pytz
import requests
import threading
import time as pytime
from datetime import datetime
from flask import Flask, render_template
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमचे धन डिटेल्स ---
CLIENT_ID = "1105760761"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9..." # तुमचा पूर्ण टोकन इथे ठेवा

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
    except: 
        pass

def check_strategy_loop():
    send_telegram("✅ *Trading Bot Started!* Checking signals every minute...")
    
    while True:
        try:
            now_ist = datetime.now(IST)
            today = now_ist.strftime('%Y-%m-%d')
            
            for stock in WATCHLIST:
                # --- Connection Error टाळण्यासाठी Retry Logic ---
                data = None
                for attempt in range(3): 
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
                    except:
                        pytime.sleep(2)

                # --- डेटा चेक आणि सिग्नल लॉजिक ---
                if data and data.get('status') == 'success' and 'data' in data:
                    d = data['data']
                    # खात्री करा की किमान २ कॅंडल्सचा डेटा आहे
                    if 'open' in d and len(d['open']) >= 2:
                        # शेवटून दुसरी कॅंडल (Previous) आणि शेवटची कॅंडल (Current)
                        prev_o = float(d['open'][-2])
                        prev_c = float(d['close'][-2])
                        curr_o = float(d['open'][-1])
                        curr_c = float(d['close'][-1])
                        candle_id = d['start_Time'][-1]
                        
                        res = None
                        
                        # --- सुधारित लॉजिक (Body to Body) ---
                        # BUY: आदल्या रेड कॅंडलच्या 'ओपन'च्या वर क्लोजिंग मिळाले तर
                        if prev_o > prev_c and curr_c > prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'BUY'}
                        
                        # SELL: आदल्या ग्रीन कॅंडलच्या 'ओपन'च्या खाली क्लोजिंग मिळाले तर
                        elif prev_c > prev_o and curr_c < prev_o:
                            res = {'s': stock['symbol'], 'p': round(curr_c, 2), 'type': 'SELL'}

                        if res:
                            # डुप्लिकेट सिग्नल टाळण्यासाठी चेक
                            is_duplicate = any(x['s'] == res['s'] and x['id_t'] == candle_id for x in SIGNAL_HISTORY)
                            
                            if not is_duplicate:
                                res['t'] = now_ist.strftime('%H:%M:%S')
                                res['id_t'] = candle_id
                                SIGNAL_HISTORY.append(res)
                                
                                icon = "🚀" if res['type'] == "BUY" else "📉"
                                send_telegram(f"{icon} *{res['type']} ALERT*\n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")
                                print(f"SIGNAL SENT: {res['s']} {res['type']}")

                # दोन स्टॉकच्या मध्ये छोटा गॅप (Rate limit टाळण्यासाठी)
                pytime.sleep(1)

        except Exception as e:
            print(f"Loop Error: {e}")
        
        # पुढच्या मिनिटासाठी वाट पाहणे
        pytime.sleep(60)

# Thread सुरू करणे
threading.Thread(target=check_strategy_loop, daemon=True).start()

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    return render_template('index.html', history=SIGNAL_HISTORY[::-1], market_open=True, date=now_ist.strftime('%d-%m-%Y'), time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
