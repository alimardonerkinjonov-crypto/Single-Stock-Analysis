# =============================================================================
# SINGLE STOCK ANALYSIS
# =============================================================================
# This script analyzes one selected stock over a user-defined date range.
# It downloads market data, calculates daily returns, exports results, and
# creates price, volume, trend, candlestick, and Bollinger Band charts.

# Import key libraries and modules.
import datetime as dt
import os
import re

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from pathlib import Path
# =============================================================================
# CONFIGURATION
# =============================================================================
# Folder where all CSV, PNG, and HTML outputs will be saved.
# Setup the exact target folder destination path [CHANGE THIS TO YOUR OWN FOLDER PATH]
desktop_path = Path.home() / "Desktop"
OUTPUT_FOLDER = desktop_path / "Single Stock Analysis."
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Accepted positive answers when confirming the matched company.
AFFIRMATIVES = {
    "y", "yes", "yeah", "yep", "yea", "yup", "ja", "ok", "okay", "sure",
    "correct", "affirmative", "exactly", "that's right", "thats right",
    "you got it", "right on", "absolutely", "definitely", "indeed",
    "totally", "right", "true", "perfect", "fine", "certainly",}
# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def safe_filename(text):
    """Convert a chart title or company name into a safe file name."""
    cleaned_text = re.sub(r"[^\w\s.-]", "", text)
    cleaned_text = re.sub(r"\s+", "_", cleaned_text.strip())
    return cleaned_text.lower()

def build_output_path(filename):
    """Create a full path inside the configured output folder."""
    return os.path.join(OUTPUT_FOLDER, filename)

def get_confirmed_company():
    """Ask for a company name/ticker, search Yahoo Finance, and confirm the match."""
    while True:
        company_input = input(
            "\nEnter the company name or ticker symbol "
            "(e.g., Apple (AAPL), Microsoft (MSFT), Tesla (TSLA)): "
        ).strip()

        try:
            search_result = yf.Search(company_input, max_results=1)

            if not search_result.quotes:
                print(f"[NOTICE] Could not find any ticker for '{company_input}'. Please try again.")
                continue

            first_match = search_result.quotes[0]

            if "symbol" not in first_match:
                print(f"[NOTICE] Data found for '{company_input}' is incomplete. Please try again.")
                continue

            ticker_symbol = first_match["symbol"]
            exact_company_name = (
                first_match.get("longName")
                or first_match.get("shortName")
                or first_match.get("name")
                or company_input
            )

            print(f"System matched your input to: '{exact_company_name}' ({ticker_symbol})")
            confirm = input("Is this the company name and ticker you meant? (y/n): ").strip().lower()

            if confirm not in AFFIRMATIVES:
                print("[NOTICE] Got it. Let's try again with different keywords.")
                continue

            print(f"-> Successfully confirmed: {exact_company_name} ({ticker_symbol})")
            return ticker_symbol, exact_company_name

        except Exception as e:
            print(f"[NOTICE] Connection error: {e}. Let's try that entry again.")


def get_date_range():
    """Ask for start/end dates and validate the format and chronological order."""
    while True:
        start_date_input = input("\nEnter the start date for the stock data (YYYY-MM-DD): ").strip()
        end_date_input = input("Enter the end date for the stock data (YYYY-MM-DD): ").strip()

        try:
            start_date = dt.datetime.strptime(start_date_input, "%Y-%m-%d")
            end_date = dt.datetime.strptime(end_date_input, "%Y-%m-%d")

            if start_date >= end_date:
                print("[NOTICE] Start date must be earlier than end date. Please try again.")
                continue

            return start_date, end_date

        except ValueError:
            print("[NOTICE] Dates must use the YYYY-MM-DD format. Please try again.")


def download_stock_data(ticker_symbol, start_date, end_date):
    """Download historical stock data and add the daily return column."""
    print(f"\nDownloading market data for: {ticker_symbol}...")
    stock = yf.download(
        ticker_symbol,
        start=start_date,
        end=end_date,
        multi_level_index=False,
        auto_adjust=False,
    )

    stock["Daily Return"] = stock["Adj Close"].pct_change(1).fillna(0) * 100
    return stock


def save_dataframe_to_csv(df, filename):
    """Save a DataFrame to the output folder."""
    csv_path = build_output_path(filename)
    df.to_csv(csv_path, index=True)
    print(f"Saved CSV file to folder: {csv_path}")
    return csv_path


def save_plotly_figure(fig, filename_base, save_png=False, show=True):
    """Save a Plotly figure as HTML, optionally also saving a PNG image."""
    html_path = build_output_path(f"{filename_base}.html")
    fig.write_html(html_path)
    print(f"Saved interactive HTML chart to folder: {html_path}")

    if save_png:
        png_path = build_output_path(f"{filename_base}.png")
        try:
            fig.write_image(png_path, width=1200, height=600, scale=3)
            print(f"Saved static PNG chart to folder: {png_path}")
        except Exception as e:
            print(f"[NOTICE] Could not save PNG image. HTML was saved successfully. Details: {e}")

    if show:
        fig.show()


def plot_finance_data(df, title, save_png=True):
    """Create a multi-line Plotly chart for one or more DataFrame columns."""
    fig = px.line(title=title)

    for column in df.columns:
        fig.add_scatter(x=df.index, y=df[column], name=column)

    fig.update_traces(line=dict(width=2))
    fig.update_layout(plot_bgcolor="white")

    save_plotly_figure(fig, safe_filename(title), save_png=save_png)


def percentage_return_classifier(percentage_return):
    """Classify daily return values into plain-English market movement groups."""
    if -0.3 < percentage_return < 0.3:
        return "Insignificant Change"
    if 0.3 < percentage_return <= 3:
        return "Positive Change"
    if -3 < percentage_return <= -0.3:
        return "Negative Change"
    if 3 < percentage_return <= 7:
        return "Large Positive Change"
    if -7 < percentage_return <= -3:
        return "Large Negative Change"
    if percentage_return > 7:
        return "Bull Run"
    return "Bear Selloff"


def plot_trend_distribution(stock):
    """Create and save a pie chart showing the distribution of trend categories."""
    trend_summary = stock["Trend"].value_counts()
    print(trend_summary)

    def clean_labels(pct):
        return f"{pct:.1f}%" if pct > 2 else ""

    plt.figure(figsize=(10, 10))
    plt.pie(
        trend_summary,
        labels=trend_summary.index,
        autopct=clean_labels,
        startangle=140,
        pctdistance=0.85,
    )
    plt.title("Distribution of Trend Categories")
    plt.tight_layout()

    pie_chart_path = build_output_path("trend_distribution_pie_chart.png")
    plt.savefig(pie_chart_path, bbox_inches="tight", dpi=300)
    print(f"Saved pie chart image to folder: {pie_chart_path}")
    plt.show()


def add_moving_averages(stock):
    """Add moving averages used by the candlestick and Bollinger Band charts."""
    stock["20-day SMA"] = stock["Close"].rolling(window=20).mean()
    stock["50-day SMA"] = stock["Close"].rolling(window=50).mean()
    return stock


def add_bollinger_bands(stock):
    """Add Bollinger Band columns based on the 20-day moving average."""
    stock["20-day STD"] = stock["Close"].rolling(window=20).std()
    stock["Upper Band"] = stock["20-day SMA"] + (stock["20-day STD"] * 2)
    stock["Lower Band"] = stock["20-day SMA"] - (stock["20-day STD"] * 2)
    return stock


def create_candlestick_chart(stock, exact_company_name):
    """Create and save a candlestick chart with 20-day and 50-day moving averages."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=stock.index,
        open=stock["Open"],
        high=stock["High"],
        low=stock["Low"],
        close=stock["Close"],
        name=f"{exact_company_name} Candlestick",
        increasing_line_color="green",
        decreasing_line_color="red",
    ))

    fig.add_trace(go.Scatter(
        x=stock.index,
        y=stock["20-day SMA"],
        mode="lines",
        name="20-day SMA",
        line=dict(color="magenta", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=stock.index,
        y=stock["50-day SMA"],
        mode="lines",
        name="50-day SMA",
        line=dict(color="green", width=1.5),
    ))

    fig.update_layout(
        title=f"{exact_company_name} Stock Interactive Candlestick Chart with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        plot_bgcolor="white",
        xaxis_rangeslider_visible=True,
    )

    save_plotly_figure(fig, f"{safe_filename(exact_company_name)}_stock_candlestick_chart", save_png=False)


def create_bollinger_bands_chart(stock, exact_company_name):
    """Create and save a candlestick chart with Bollinger Bands."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=stock.index,
        open=stock["Open"],
        high=stock["High"],
        low=stock["Low"],
        close=stock["Close"],
        name=f"{exact_company_name} Candlestick",
        increasing_line_color="green",
        decreasing_line_color="red",
    ))

    fig.add_trace(go.Scatter(
        x=stock.index,
        y=stock["20-day SMA"],
        mode="lines",
        name="20-day SMA",
        line=dict(color="blue", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=stock.index,
        y=stock["Upper Band"],
        mode="lines",
        name="Upper Band",
        line=dict(color="red", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=stock.index,
        y=stock["Lower Band"],
        mode="lines",
        name="Lower Band",
        line=dict(color="red", width=1.5),
    ))

    fig.update_layout(
        title=f"{exact_company_name} Stock Interactive Candlestick Chart with Bollinger Bands",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        plot_bgcolor="white",
        xaxis_rangeslider_visible=True,
    )

    save_plotly_figure(
        fig,
        f"{safe_filename(exact_company_name)}_stock_candlestick_chart_with_bollinger_bands",
        save_png=False,
    )


# =============================================================================
# MAIN SCRIPT
# =============================================================================

# 1. Collect inputs and download stock data.
ticker_symbol, exact_company_name = get_confirmed_company()
start_date, end_date = get_date_range()
stock = download_stock_data(ticker_symbol, start_date, end_date)

# 2. Save and inspect the prepared market dataset.
csv_filename = f"{safe_filename(exact_company_name)}_market_data_and_daily_returns.csv"
save_dataframe_to_csv(stock, csv_filename)

print("\n--- Stock Data Preview ---")
print(stock.head())

print("\n--- Stock Data Summary ---")
print(stock.describe().round(2))

max_return = stock["Daily Return"].max()
print(f"\nMaximum Daily Return: {max_return:.2f}%")

# 3. Create basic price and return charts.
fig_adj_close = px.line(
    stock,
    y="Adj Close",
    title=f"{exact_company_name} Stock Adjusted Close Price [$]",
)
save_plotly_figure(
    fig_adj_close,
    f"{safe_filename(ticker_symbol)}_stock_adjusted_close_price_line_graph",
    save_png=False,
)

plot_finance_data(stock[["Volume"]], f"{exact_company_name} Stock Trading Volume")
plot_finance_data(
    stock.drop(["Daily Return", "Volume"], axis=1),
    f"{exact_company_name} Stock Price Data",
)
plot_finance_data(
    stock[["Adj Close", "Daily Return"]],
    f"{exact_company_name} Stock Adjusted Close Price and Daily Return",
)

# 4. Classify daily returns and visualize the trend distribution.
stock["Trend"] = stock["Daily Return"].apply(percentage_return_classifier)
plot_trend_distribution(stock)

# 5. Add technical indicators and create advanced interactive charts.
stock = add_moving_averages(stock)
stock = add_bollinger_bands(stock)
create_candlestick_chart(stock, exact_company_name)
create_bollinger_bands_chart(stock, exact_company_name)
