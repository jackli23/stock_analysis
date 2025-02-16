import streamlit as st
import yfinance as yf
import pandas as pd
import ta  # For technical indicators
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from newsapi import NewsApiClient

# Set up NewsAPI with your API key
NEWSAPI_KEY = "c3e19cfaf7754189a360129571583112"
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)

# Function to fetch stock data
def fetch_stock_data(stock_ticker, start="2020-01-01"):
    stock_data = yf.Ticker(stock_ticker)
    df = stock_data.history(period="1d", start=start, end=None)
    return df

# Function to fetch stock news from NewsAPI
def fetch_stock_news(stock_ticker):
    try:
        news = newsapi.get_everything(q=stock_ticker, language="en", sort_by="publishedAt")
        articles = news["articles"][:5]  # Get top 5 articles
        return [{"title": a["title"], "link": a["url"]} for a in articles]
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []

# Fallback: Web Scraper for Yahoo Finance News
def fetch_stock_news_scraper(stock_ticker):
    url = f"https://finance.yahoo.com/quote/{stock_ticker}/news"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
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
        print(f"Error fetching Yahoo Finance news: {e}")
        return []

# Function to calculate indicators and buy/sell signals
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

# Function to plot stock price with buy/sell signals
def plot_stock(df, stock_ticker):
    fig, ax = plt.subplots(figsize=(10, 5))

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

    st.pyplot(fig)

    # Buy/Sell Analysis Summary
    last_row = df.iloc[-1]
    if last_row["Buy_Signal"]:
        st.success(f"✅ **BUY Signal for {stock_ticker}.** 50-day SMA has crossed above 200-day SMA.")
    elif last_row["Sell_Signal"]:
        st.warning(f"⚠️ **SELL Signal for {stock_ticker}.** 50-day SMA has crossed below 200-day SMA.")
    else:
        st.info(f"📊 **No clear Buy/Sell signals for {stock_ticker}.** Market remains neutral.")

# Streamlit UI
st.title("📈 Multi-Stock Analysis & Buy/Sell Signals")

# Sidebar for stock selection
selected_stocks = st.sidebar.text_area("Enter stock tickers (comma-separated)", "AAPL, TSLA, GOOG")
start_date = st.sidebar.date_input("Start Date", datetime(2020, 1, 1))

if st.sidebar.button("Analyze Stocks"):
    stock_list = [stock.strip().upper() for stock in selected_stocks.split(",")]

    for stock in stock_list:
        st.subheader(f"📊 {stock} Analysis")

        # Fetch stock data
        df = fetch_stock_data(stock, start=start_date.strftime("%Y-%m-%d"))
        if df.empty:
            st.error(f"No data found for {stock}. Check the ticker symbol.")
        else:
            df = analyze_stock(df)
            plot_stock(df, stock)

        # Fetch stock news
        st.subheader(f"📰 Latest News for {stock}")
        news_articles = fetch_stock_news(stock)

        if not news_articles:
            news_articles = fetch_stock_news_scraper(stock)  # Fallback to Yahoo Finance scraping

        if news_articles:
            for article in news_articles:
                st.markdown(f"🔹 [{article['title']}]({article['link']})")
        else:
            st.write("No recent news found.")