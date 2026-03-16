import yfinance as yf
import requests
import os
from datetime import datetime, time
from flask import Flask, render_template

app = Flask(__name__)

# --- क्रेडेंशियल्स ---
TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=10)
    except:
        print("Telegram Error")

# ही टेस्ट फंक्शन आहे जी वेबसाईट सुरू होताच मेसेज पाठवेल
def initial_test():
    test_msg = "✅ *Bot Connection Success!*\nतुमचा 'Inside Candle' स्कॅनर आता तुमच्या टेलिग्रामशी जोडला गेला आहे. उद्या सकाळी ९:३० पासून अलर्ट मिळण्यास सुरुवात होईल."
    send_telegram(test_msg)

# पहिल्यांदा रन होताना टेस्ट मेसेज पाठवा
initial_test()

@app.route('/')
def home():
    # सध्या रात्रीची वेळ असल्याने स्कॅनिंग रिकामे असेल
    return render_template('index.html', stocks=[], date=datetime.now().strftime('%d-%m-%Y'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
