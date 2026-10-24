"""Download and analyze five years of daily Apple and Microsoft stock data."""

from datetime import date, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TICKERS = ["AAPL", "MSFT"]
TODAY = date.today()
START_DATE = (pd.Timestamp(TODAY) - pd.DateOffset(years=5)).date().isoformat()
END_DATE = (TODAY + timedelta(days=1)).isoformat()  # yfinance end dates are exclusive.


def download_market_data(
    tickers: list[str] = TICKERS,
    start: str = START_DATE,
    end: str = END_DATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download adjusted and unadjusted closing prices plus trading volume."""
    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=False,
        group_by="ticker",
        multi_level_index=True,
        progress=False,
        threads=False,
    )
    if raw is None or raw.empty:
        raise RuntimeError("No stock data was returned. Check the ticker symbols and try again later.")
    if not isinstance(raw.columns, pd.MultiIndex):
        raise RuntimeError("Expected multi-ticker data with a two-level column index from yfinance.")

    available = set(raw.columns.get_level_values(0))
    missing = sorted(set(tickers) - available)
    if missing:
        raise RuntimeError(f"No data was returned for: {', '.join(missing)}")

    adjusted_close = raw.xs("Adj Close", axis=1, level=1).reindex(columns=tickers)
    volume = raw.xs("Volume", axis=1, level=1).reindex(columns=tickers)
    adjusted_close = adjusted_close.dropna(how="all").sort_index()
    volume = volume.reindex(adjusted_close.index)
    adjusted_close.index = pd.DatetimeIndex(adjusted_close.index, name="Date")
    volume.index = pd.DatetimeIndex(volume.index, name="Date")
    return adjusted_close, volume


def calculate_moving_averages(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate 20- and 200-trading-day rolling averages."""
    return prices.rolling(window=20, min_periods=20).mean(), prices.rolling(window=200, min_periods=200).mean()


def resample_prices(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return last available adjusted close for each week and month."""
    weekly = prices.resample("W-FRI").last().dropna(how="all")
    monthly = prices.resample(pd.offsets.MonthEnd()).last().dropna(how="all")
    return weekly, monthly


def compare_trading_volume(volume: pd.DataFrame) -> pd.Series:
    """Compare each company's mean daily trading volume over the selected period."""
    return volume.mean().sort_values(ascending=False).rename("Average Daily Volume")


def save_results(
    prices: pd.DataFrame,
    volume: pd.DataFrame,
    weekly: pd.DataFrame,
    monthly: pd.DataFrame,
    ma20: pd.DataFrame,
    ma200: pd.DataFrame,
) -> None:
    """Save derived tables and line/bar charts to local folders."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prices.to_csv(DATA_DIR / "adjusted_close.csv")
    volume.to_csv(DATA_DIR / "trading_volume.csv")
    weekly.to_csv(OUTPUT_DIR / "weekly_adjusted_close.csv")
    monthly.to_csv(OUTPUT_DIR / "monthly_adjusted_close.csv")
    pd.concat({"MA20": ma20, "MA200": ma200}, axis=1).to_csv(OUTPUT_DIR / "moving_averages.csv")
    compare_trading_volume(volume).to_csv(OUTPUT_DIR / "average_daily_volume.csv")

    fig, ax = plt.subplots(figsize=(12, 6))
    for ticker in prices.columns:
        ax.plot(prices.index, prices[ticker], label=ticker, linewidth=1.4)
    ax.set(title="Adjusted Closing Prices", xlabel="Date", ylabel="Adjusted close (USD)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.25)
    ax.legend(title="Ticker")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "adjusted_close_prices.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(len(prices.columns), 1, figsize=(12, 5 * len(prices.columns)), sharex=True)
    if len(prices.columns) == 1:
        axes = [axes]
    for ax, ticker in zip(axes, prices.columns):
        ax.plot(prices.index, prices[ticker], label="Adjusted Close", color="#3259a8", linewidth=1.1)
        ax.plot(ma20.index, ma20[ticker], label="20-day average", color="#f39c12", linewidth=1.2)
        ax.plot(ma200.index, ma200[ticker], label="200-day average", color="#c0392b", linewidth=1.4)
        ax.set_title(f"{ticker}: Price and Moving Averages")
        ax.set_ylabel("USD")
        ax.grid(alpha=0.2)
        ax.legend()
    axes[-1].set_xlabel("Date")
    axes[-1].xaxis.set_major_locator(mdates.YearLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "moving_averages.png", dpi=160)
    plt.close(fig)

    average_volume = compare_trading_volume(volume).sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(average_volume.index, average_volume.values, color=["#168aad", "#f4a261"])
    ax.set(title="Average Daily Trading Volume", xlabel="Ticker", ylabel="Shares traded per day")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "average_daily_volume.png", dpi=160)
    plt.close(fig)


def run_analysis() -> dict[str, pd.DataFrame | pd.Series]:
    """Download data, calculate time-series summaries and save outputs."""
    prices, volume = download_market_data()
    weekly, monthly = resample_prices(prices)
    ma20, ma200 = calculate_moving_averages(prices)
    average_volume = compare_trading_volume(volume)
    save_results(prices, volume, weekly, monthly, ma20, ma200)
    return {
        "prices": prices,
        "volume": volume,
        "weekly": weekly,
        "monthly": monthly,
        "ma20": ma20,
        "ma200": ma200,
        "average_volume": average_volume,
    }


def main() -> None:
    results = run_analysis()
    prices = results["prices"]
    print(f"Downloaded {len(prices):,} trading days from {prices.index.min():%Y-%m-%d} to {prices.index.max():%Y-%m-%d}.")
    print("\nAverage daily trading volume:")
    print(results["average_volume"].map(lambda value: f"{value:,.0f}").to_string())
    print(f"\nWeekly rows: {len(results['weekly']):,} | Monthly rows: {len(results['monthly']):,}")
    print(f"Charts and summary tables saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

