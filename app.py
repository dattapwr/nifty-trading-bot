import yfinance as yf
import pandas as pd
import requests
from flask import Flask, render_template

app = Flask(_name_)

TOKEN = "8581468481:AAEkpYl2W68kUDt-unA_qvSpgTeOiXRFji8"
CHAT_ID = "799650120"

# दिवसभराचे स्टॉक्स साठवण्यासाठी मेमरी
FOUND_STOCKS_HISTORY = []

STOCK_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
    'AXISBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS', 
    'BAJFINANCE.NS', 'MARUTI.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'M&M.NS', 
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'JINDALSTEL.NS', 'HINDALCO.NS', 'HCLTECH.NS',
    'WIPRO.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'DLF.NS', 'TRENT.NS',
    'HAL.NS', 'BEL.NS', 'COALINDIA.NS', 'NT
