import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'SBIN.NS', 'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS', 'ICICIBANK.NS', 'HDFCBANK.NS']

def get_pro_pnl_backtest(start_date, end_date):
    results = []
    investment_per_trade = 50000 # प्रत्येक ट्रेडसाठी ५० हजार रुपये
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    for ticker in STOCKS:
        try:
            df = yf.download(ticker, start=start_date, end=end_dt.strftime('%Y-%m-%d'), interval='5m', progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            daily = yf.download(ticker, start=start_date, end=end_dt.strftime('%Y-%m-%d'), interval='1d', progress=False)
            df['date'] = df.index.date

            for date in df['date'].unique():
                day_df = df[df['date'] == date]
                green_vols_since_930 = []

                for i in range(1, len(day_df)):
                    curr_row = day_df.iloc[i]
                    prev_row = day_df.iloc[i-1]
                    curr_dt = curr_row.name.astimezone(IST)

                    if curr_dt.time() < datetime.strptime("09:30", "%H:%M").time(): continue

                    # १. कालच्या क्लोजिंग पेक्षा खाली
                    try:
                        prev_close = daily.loc[:curr_dt.strftime('%Y-%m-%d')].iloc[-2]['Close']
                        if float(curr_row['Close']) >= prev_close: continue
                    except: continue

                    # २. हिरवी कॅन्डल + सकाळपासूनचा Lowest Volume
                    is_green = float(prev_row['Close']) > float(prev_row['Open'])
                    if is_green:
                        current_vol = float(prev_row['Volume'])
                        is_lowest = not green_vols_since_930 or current_vol < min(green_vols_since_930)
                        green_vols_since_930.append(current_vol)

                        # ३. लाल ब्रेकआउट
                        is_red = float(curr_row['Close']) < float(curr_row['Open'])
                        breakout = float(curr_row['Close']) < float(prev_row['Low'])

                        if is_red and breakout and is_lowest:
                            entry = float(curr_row['Close'])
                            sl = float(prev_row['High'])
                            target = entry - ((sl - entry) * 2)
                            qty = int(investment_per_trade / entry) # क्वांटिटी कॅल्क्युलेशन
                            
                            outcome = "Wait.."
                            profit_loss = 0
                            
                            for j in range(i + 1, len(day_df)):
                                if float(day_df.iloc[j]['High']) >= sl:
                                    outcome = "SL ❌"
                                    profit_loss = -(sl - entry) * qty
                                    break
                                if float(day_df.iloc[j]['Low']) <= target:
                                    outcome = "Target ✅"
                                    profit_loss = (entry - target) * qty
                                    break

                            results.append({
                                't': curr_dt.strftime('%d-%m %H:%M'),
                                's': ticker,
                                'p': round(entry, 2),
                                'res': outcome,
                                'pnl': round(profit_loss, 2),
                                'qty': qty
                            })
        except: continue
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    bt_results = get_pro_pnl_backtest(start, end) if start and end else []
    
    total_pnl = sum(r['pnl'] for r in bt_results)
    wins = len([r for r in bt_results if "Target" in r['res']])
    total_trades = len([r for r in bt_results if "Wait" not in r['res']])
    win_rate = round((wins / total_trades) * 100, 2) if total_trades > 0 else 0

    return render_template('index.html', bt_results=bt_results, total_pnl=total_pnl, win_rate=win_rate)

if __name__ == "__main__":
    app.run()
