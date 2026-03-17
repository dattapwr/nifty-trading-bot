import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# बैकटेस्ट के लिए उपलब्ध स्टॉक्स की लिस्ट
AVAILABLE_STOCKS = ['TATAMOTORS.NS', 'RELIANCE.NS', 'SBIN.NS', 'INFY.NS', 'TCS.NS', 'ITC.NS', 'LT.NS', 'ICICIBANK.NS', 'HDFCBANK.NS', 'M&M.NS', 'AXISBANK.NS']

def get_optimized_pnl_report(selected_stocks, start_date, end_date):
    results = []
    investment = 50000 
    brokerage = 40 
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    for ticker in selected_stocks:
        try:
            df = yf.download(ticker, start=start_date, end=end_dt.strftime('%Y-%m-%d'), interval='5m', progress=False, threads=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            daily = yf.download(ticker, start=start_date, end=end_dt.strftime('%Y-%m-%d'), interval='1d', progress=False)
            df['date'] = df.index.date
            tv_symbol = f"NSE:{ticker.replace('.NS', '')}"

            for date in df['date'].unique():
                day_df = df[df['date'] == date].copy()
                green_vols = []

                for i in range(1, len(day_df)):
                    curr_row = day_df.iloc[i]
                    prev_row = day_df.iloc[i-1]
                    curr_dt = curr_row.name.astimezone(IST)

                    if curr_dt.time() < datetime.strptime("09:30", "%H:%M").time(): continue

                    # नेगेटिव ट्रेंड चेक
                    try:
                        prev_close = daily.loc[:curr_dt.strftime('%Y-%m-%d')].iloc[-2]['Close']
                        if float(curr_row['Close']) >= prev_close: continue
                    except: continue

                    # सकाळपासूनची Lowest Volume Green Candle
                    is_green = float(prev_row['Close']) > float(prev_row['Open'])
                    if is_green:
                        v = float(prev_row['Volume'])
                        is_lowest = not green_vols or v < min(green_vols)
                        green_vols.append(v)

                        # ब्रेकआउट (लाल कैंडल द्वारा लो तोड़ना)
                        if float(curr_row['Close']) < float(curr_row['Open']) and \
                           float(curr_row['Close']) < float(prev_row['Low']) and is_lowest:
                            
                            entry = float(curr_row['Close'])
                            sl = float(prev_row['High'])
                            target = entry - ((sl - entry) * 2)
                            qty = int(investment / entry)
                            
                            outcome, pnl = "Wait..", 0
                            for j in range(i + 1, len(day_df)):
                                if float(day_df.iloc[j]['High']) >= sl:
                                    outcome, pnl = "SL ❌", -(sl - entry) * qty - brokerage
                                    break
                                if float(day_df.iloc[j]['Low']) <= target:
                                    outcome, pnl = "TGT ✅", (entry - target) * qty - brokerage
                                    break

                            results.append({
                                't': curr_dt.strftime('%d-%b %H:%M'),
                                's': ticker,
                                'p': round(entry, 2),
                                'res': outcome,
                                'pnl': round(pnl, 2),
                                'tv_url': f"https://www.tradingview.com/chart/?symbol={tv_symbol}"
                            })
        except: continue
    return sorted(results, key=lambda x: x['t'], reverse=True)

@app.route('/')
def home():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    selected = request.args.getlist('stocks')
    
    bt_results = get_optimized_pnl_report(selected, start, end) if start and end and selected else []
    total_pnl = sum(r['pnl'] for r in bt_results)
    
    return render_template('index.html', bt_results=bt_results, total_pnl=total_pnl, available_stocks=AVAILABLE_STOCKS)

if __name__ == "__main__":
    app.run()
