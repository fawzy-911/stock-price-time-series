# Stock Price Time Series Analysis

Download five years of historical data for Apple (`AAPL`) and Microsoft (`MSFT`), then explore adjusted closing prices, weekly/monthly resampling, rolling averages, and trading volume with Pandas and Matplotlib.

**Roadmap project:** <https://roadmap.sh/projects/stock-price-time-series>

## Run the analysis

Python 3.10 or later is recommended. The project downloads current historical data when run, so it needs an internet connection.

```bash
python -m venv .venv
```

Activate the environment, install requirements, and run:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

python -m pip install -r requirements.txt
python stock_analysis.py
```

To work through the same analysis interactively:

```bash
jupyter notebook stock_price_analysis.ipynb
```

The project uses `yfinance.download()` for both tickers, keeps the date index, and selects adjusted close prices for comparisons. It resamples to Friday-ending weeks and month ends, calculates 20- and 200-trading-day rolling averages, and compares average daily share volume.

## Generated files

- `data/adjusted_close.csv` and `data/trading_volume.csv`
- `outputs/weekly_adjusted_close.csv` and `outputs/monthly_adjusted_close.csv`
- `outputs/moving_averages.csv` and `outputs/average_daily_volume.csv`
- `outputs/adjusted_close_prices.png`, `outputs/moving_averages.png`, and `outputs/average_daily_volume.png`

Market data is downloaded locally when you run the analysis and is not committed to the repository. `yfinance` is an open-source interface to Yahoo Finance data; review the data provider's terms for your intended use.

