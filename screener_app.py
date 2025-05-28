
import streamlit as st
import pandas as pd
import requests
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
import plotly.graph_objects as go

st.set_page_config(page_title="Real-Time Stock Screener", layout="wide")
st.title("📈 Nifty500 Real-Time Screener")

@st.cache_data(ttl=600)
def load_data():
    url = "https://assets.upstox.com/market-quote/instruments/exchange/nse_eq.csv"
    df = pd.read_csv(url)
    df = df[df['instrument_key'].str.contains("NSE_EQ")]
    return df

@st.cache_data(ttl=600)
def load_nifty500_keys():
    return pd.read_csv("nifty500_instrument_keys.csv")

@st.cache_data(ttl=600)
def fetch_historical_data(instrument_key, interval='1d', limit=200):
    headers = {"Authorization": f"Bearer {st.secrets['UPSTOX_TOKEN']}"}
    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}?limit={limit}"
    response = requests.get(url, headers=headers)
    data = response.json()
    candles = data['data']['candles']
    df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"])
    return df

def screen_stocks(instruments):
    results = []
    for _, row in instruments.iterrows():
        try:
            df = fetch_historical_data(row['instrument_key'])
            ema20 = EMAIndicator(df['close'], window=20).ema_indicator()
            ema50 = EMAIndicator(df['close'], window=50).ema_indicator()
            rsi = RSIIndicator(df['close']).rsi()

            if ema20.iloc[-1] > ema50.iloc[-1] and rsi.iloc[-1] < 70:
                results.append({
                    "Symbol": row["symbol"],
                    "Name": row["instrument_key"],
                    "EMA20": round(ema20.iloc[-1], 2),
                    "EMA50": round(ema50.iloc[-1], 2),
                    "RSI": round(rsi.iloc[-1], 2)
                })
        except Exception:
            continue
    return pd.DataFrame(results)

with st.spinner("Loading instruments..."):
    all_instruments = load_data()
    nifty500_keys = load_nifty500_keys()
    instruments = all_instruments[all_instruments["instrument_key"].isin(nifty500_keys["instrument_key"])]

if st.button("🔍 Run Screener"):
    with st.spinner("Screening stocks..."):
        screened = screen_stocks(instruments)
        st.success(f"Found {len(screened)} matching stocks!")
        st.dataframe(screened)
