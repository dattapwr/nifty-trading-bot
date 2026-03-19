import os
from flask import Flask, render_template_string
from dhanhq import dhanhq

app = Flask(__name__)

# --- तुमची माहिती ---
CLIENT_ID = "1105760761"
# तुमचा सर्वात नवीन टोकन इथे टाका
ACCESS_TOKEN = "तुमचा_टोकन_इथे_टाका"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

@app.route('/')
def home():
    price = "शोधत आहे..."
    status_color = "#f1c40f"
    
    try:
        # क्रूड ऑईल मार्च फ्युचरसाठी थेट कॉल
        resp = dhan.get_quote('420844', 'MCX')
        
        if resp and resp.get('status') == 'success':
            price = f"₹{resp['data'].get('last_price')}"
            status_color = "#2ecc71"
        else:
            price = "टोकन एरर"
            status_color = "#e74c3c"
    except Exception as e:
        price = "कनेक्शन एरर"
        status_color = "#e74c3c"

    return render_template_string("""
    <body style="background:#1a1a2e; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
        <div style="display:inline-block; background:#16213e; padding:50px; border-radius:30px; border:2px solid {{color}};">
            <h2 style="color:#8892b0;">CRUDE OIL MAR FUT</h2>
            <h1 style="font-size:80px; margin:20px; color:{{color}};">{{price}}</h1>
            <p style="color:#533483;">Auto-refreshing...</p>
        </div>
        <script>setTimeout(function(){ location.reload(); }, 5000);</script>
    </body>
    """, price=price, color=status_color)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
