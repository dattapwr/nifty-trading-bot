import os
import pytz
import requests
from datetime import datetime, time
from flask import Flask, render_template
from dhanhq import dhanhq
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# --- तुमचे धन डिटेल्स ---
CLIENT_ID = "1105760761"
# तुम्ही दिलेला नवीन टोकन इथे अपडेट केला आहे
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzczOTAxNzcwLCJpYXQiOjE3NzM4MTUzNzAsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.IxHMt3yaFEGdmNmD0OoJRQ4LI0_74gicUNJMxRgMQP7ca7qrEokD5KZ9ssWfZUtKMhOcfKWZ7_G7cZH_QdkacA"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# Telegram Details
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"
IST = pytz.timezone('Asia/Kolkata')

SIGNAL_HISTORY = []

# --- १८ मार्च २०२६ साठीचे IDs ---
WATCHLIST = [
    {'symbol': 'CRUDEOIL MAR FUT', 'sid': '64115'}, #
    {'symbol': 'NATURALGAS MAR FUT', 'sid': '64132'} #
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: 
        requests.get(url, params=params, timeout=5)
    except: 
        pass

def check_strategy():
    now_ist = datetime.now(IST)
    # मार्केट वेळ ९ ते रात्री ११:३०
    if not (time(9, 0) <= now_ist.time() <= time(23, 30)):
        return

    for stock in WATCHLIST:
        try:
            data = dhan.get_intraday_data(
                security_id=stock['sid'],
                exchange_segment='MCX_FO', #
                instrument_type='FUTCOM',
                interval=1, 
                from_date=now_ist.strftime('%Y-%m-%d'),
                to_date=now_ist.strftime('%Y-%m-%d')
            )

            if data.get('status') == 'success' and 'data' in data:
                d = data['data']
                if len(d['open']) < 3: 
                    continue

                # मागील पूर्ण झालेली कॅंडल (Index -2) | चालू किंमत (Index -1)
                prev_o, prev_c = float(d['open'][-2]), float(d['close'][-2])
                curr_c = float(d['close'][-1])
                
                candle_id = d['start_Time'][-1]
                display_time = now_ist.strftime('%H:%M:%S')

                # --- तुमच्या चित्राप्रमाणे केवळ बॉडी रिव्हर्सल लॉजिक ---
                res = None
                # BUY: मागील Red, चालू किंमत तिच्या Open च्या वर
                if prev_o > prev_c and curr_c > prev_o:
                    res = {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'BUY'}
                # SELL: मागील Green, चालू किंमत तिच्या Open च्या खाली
                elif prev_c > prev_o and curr_c < prev_o:
                    res = {'s': stock['symbol'], 'p': round(curr_c, 2), 't': display_time, 'id_t': candle_id, 'type': 'SELL'}

                if res:
                    # डुप्लिकेट टाळण्यासाठी चेक
                    if not any(x['s'] == res['s'] and x['type'] == res['type'] and x['id_t'] == res['id_t'] for x in SIGNAL_HISTORY):
                        SIGNAL_HISTORY.append(res)
                        icon = "🚀" if res['type'] == "BUY" else "📉"
                        send_telegram(f"{icon} *{res['type']} ALERT*\n\nStock: `{res['s']}`\nPrice: ₹{res['p']}\nTime: {res['t']}")
                        print(f"Signal Sent: {res['s']} {res['type']}") # हे रेंडर लॉन्समध्ये दिसेल

        except Exception as e:
            print(f"Error checking {stock['symbol']}: {e}")

# --- बॅकग्राउंड टायमर सुरू करा ---
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=check_strategy, trigger="interval", seconds=60)
scheduler.start()

@app.route('/')
def home():
    now_ist = datetime.now(IST)
    return render_template('index.html', history=SIGNAL_HISTORY[::-1], 
                           date=now_ist.strftime('%d-%m-%Y'), 
                           time=now_ist.strftime('%H:%M:%S'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # रेंडरवर scheduler नीट चालण्यासाठी use_reloader=False ठेवा
    app.run(host='0.0.0.0', port=port, use_reloader=False)
