import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta  # For technical indicators
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# Function to fetch stock data
def fetch_stock_data(stock_ticker, start="2025-01-01"):
    stock_data = yf.Ticker(stock_ticker)
    df = stock_data.history(period="1d", start=start, end=None)
    return df

# Function to fetch stock news from Yahoo Finance
import yfinance as yf

import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup

def fetch_stock_news(stock_ticker):
    url = f"https://finance.yahoo.com/quote/{stock_ticker}/news"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Yahoo may have changed its structure, so let's look for <h3> tags directly
        articles = soup.find_all("h3")

        news_list = []
        for article in articles[:5]:  # Get top 5 articles
            title = article.text.strip()
            link_tag = article.find("a")
            if link_tag and "href" in link_tag.attrs:
                link = "https://finance.yahoo.com" + link_tag["href"]
                news_list.append({"title": title, "link": link})

        return news_list if news_list else []

    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return []

# Function to calculate indicators and generate buy/sell signals
def analyze_stock(df):
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

    # MACD Indicator
    df["MACD"] = ta.trend.MACD(df["Close"]).macd()
    df["MACD_Signal"] = ta.trend.MACD(df["Close"]).macd_signal()

    # Buy & Sell signals based on SMA crossover strategy
    df["Buy_Signal"] = (df["SMA_50"] > df["SMA_200"]) & (df["SMA_50"].shift(1) <= df["SMA_200"].shift(1))
    df["Sell_Signal"] = (df["SMA_50"] < df["SMA_200"]) & (df["SMA_50"].shift(1) >= df["SMA_200"].shift(1))

    return df

# Function to plot stock price with indicators and comments
def plot_stock(df, stock_ticker):
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df.index, df["Close"], label="Closing Price", color="blue")
    ax.plot(df.index, df["SMA_50"], label="50-day SMA", linestyle="dashed", color="orange")
    ax.plot(df.index, df["SMA_200"], label="200-day SMA", linestyle="dashed", color="red")

    # Mark buy/sell signals
    ax.scatter(df.index[df["Buy_Signal"]], df["Close"][df["Buy_Signal"]], marker="^", color="green", label="Buy Signal", s=100)
    ax.scatter(df.index[df["Sell_Signal"]], df["Close"][df["Sell_Signal"]], marker="v", color="red", label="Sell Signal", s=100)

    ax.set_title(f"{stock_ticker} Price & Buy/Sell Signals")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    
    # Analysis Comment
    last_row = df.iloc[-1]
    comment = "📉 No clear buy/sell signals detected." if not last_row["Buy_Signal"] and not last_row["Sell_Signal"] else \
              "📊 BUY signal detected!" if last_row["Buy_Signal"] else "⚠️ SELL signal detected!"
    
    plt.figtext(0.5, 0.02, comment, ha="center", fontsize=12, bbox={"facecolor": "yellow", "alpha": 0.3, "pad": 5})
    st.pyplot(fig)

# Streamlit UI
st.title("📈 Stock Analysis & News Feed App")

# Sidebar for stock selection
selected_stock = st.sidebar.text_input("Enter a stock ticker (e.g., AAPL, TSLA)", "GOOG")
start_date = st.sidebar.date_input("Start Date", datetime(2025, 1, 1))

if st.sidebar.button("Analyze Stock"):
    df = fetch_stock_data(selected_stock, start=start_date.strftime("%Y-%m-%d"))

    if df.empty:
        st.error("No data found. Please check the stock ticker and try again.")
    else:
        df = analyze_stock(df)
        
        # Display stock chart
        plot_stock(df, selected_stock)

        # Show latest signals
        last_row = df.iloc[-1]
        if last_row["Buy_Signal"]:
            st.success(f"✅ **BUY Signal detected for {selected_stock}**")
        elif last_row["Sell_Signal"]:
            st.warning(f"⚠️ **SELL Signal detected for {selected_stock}**")
        else:
            st.info(f"📊 **No clear Buy/Sell signals for {selected_stock} right now.**")

# Display Stock News
st.subheader(f"📰 Latest News for {selected_stock}")
news_articles = fetch_stock_news(selected_stock)

if news_articles:
    for article in news_articles:
        st.markdown(f"🔹 [{article['title']}]({article['link']})")
else:
    st.write("No recent news found.")