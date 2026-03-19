import os
import pytz
import requests
from datetime import datetime
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- धन क्रेडेंशियल्स ---
CLIENT_ID = "1105760761"
# खालील टोकनच्या जागी तुमचा नवीन 'Market Data' परमिशन असलेला टोकन टाका
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc0MDExMTM4LCJpYXQiOjE3NzM5MjQ3MzgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1NzYwNzYxIn0.InHFl8iccMYs5Smf5XZ9M_GeCehcZYnuh5NAbcMN-6N7vzNLP7qb8jdLNpSbqyue3TXuxKGd-TmK4FVwfD3jKQ"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
IST = pytz.timezone('Asia/Kolkata')

# टेलिग्राम डिटेल्स
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

def get_crude_data():
    """थेट लाईव्ह भाव ओढण्यासाठीचे फंक्शन"""
    try:
        # ४२०८४४ = MCX CRUDE OIL MAR FUT
        resp = dhan.get_quote(security_id='420844', exchange_segment='MCX')
        
        if resp and resp.get('status') == 'success':
            price = resp['data'].get('last_price')
            return {"CRUDE OIL MAR FUT": price}
        else:
            print(f"Dhan API Error: {resp}")
            return {}
    except Exception as e:
        print(f"Technical Error: {e}")
        return {}

@app.route('/')
def home():
    prices = get_crude_data()
    now = datetime.now(IST).strftime('%H:%M:%S')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="10">
        <title>Crude Oil Live</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: white; text-align: center; padding-top: 50px; }
            .container { background: #1e293b; display: inline-block; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }
            h1 { color: #38bdf8; margin-bottom: 5px; }
            .price { font-size: 64px; font-weight: bold; color: #22c55e; margin: 20px 0; }
            .symbol { color: #94a3b8; font-size: 18px; }
            .error { color: #ef4444; background: #450a0a; padding: 15px; border-radius: 10px; margin-top: 20px; }
            .sync { color: #64748b; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛢️ Crude Oil Monitor</h1>
            <p class="sync">Last Sync: {{ last_time }}</p>
            <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">
            
            {% for s, p in ltp.items() %}
                <div class="symbol">{{ s }}</div>
                <div class="price">₹{{ p }}</div>
            {% else %}
                <div class="error">
                    <strong>🛑 डेटा येत नाहीये!</strong><br>
                    टोकन जनरेट करताना 'Market Data' टिक केल्याची खात्री करा.
                </div>
            {% endfor %}
            
            <p style="margin-top: 20px; font-size: 12px; color: #475569;">Refreshing every 10 seconds...</p>
        </div>
    </body>
    </html>
    """, ltp=prices, last_time=now)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
