import pandas as pd
import yfinance as yf

start_date = "2016-01-01"
end_date = "2026-01-01"

tickers = ["SPY", "EXSA.DE", "IEF", "LQD", "HYG", "GLD", "EURUSD=X"]

market_data = yf.download(
    tickers, start=start_date, end=end_date, interval="1d", auto_adjust=True, progress=False
)

close_prices = market_data["Close"]

print(close_prices.head())
print(close_prices.tail())
print(close_prices.shape)
print(close_prices.isna().sum())

output_path = "data/raw/market_close_prices_2016_2025.csv"

close_prices.to_csv(output_path, index=True, index_label="date")

print(f"Saved raw market data to: {output_path}")

asset_map = {
    "SPY": "US_EQUITY",
    "EXSA.DE": "EU_EQUITY",
    "IEF": "US_GOV_BOND",
    "LQD": "US_IG_CORP_BOND",
    "HYG": "US_HIGH_YIELD_BOND",
    "GLD": "GOLD",
}

close_prices.index.name = "date"
asset_prices = close_prices.drop(columns=["EURUSD=X"]).reset_index()

prices = asset_prices.melt(id_vars="date", var_name="ticker", value_name="price")
prices = prices.dropna(subset=["price"])
prices["asset_id"] = prices["ticker"].map(asset_map)
prices["currency"] = "USD"
prices.loc[prices["ticker"] == "EXSA.DE", "currency"] = "EUR"
prices = prices[["date", "asset_id", "price", "currency"]]

prices.to_csv("data/processed/prices.csv", index=False)

print(prices.head())
print(prices.tail())
print(prices.shape)

fx_rates = close_prices[["EURUSD=X"]].dropna().reset_index()

fx_rates = fx_rates.rename(columns={"EURUSD=X": "usd_per_unit"})
fx_rates["currency"] = "EUR"
fx_rates = fx_rates[["date", "currency", "usd_per_unit"]]

fx_rates.to_csv("data/processed/fx_rates.csv", index=False)


print(fx_rates.head())
print(fx_rates.tail())
print(fx_rates.shape)

common_data = close_prices.dropna()
valuation_date = common_data.index.max()
latest_market_data = common_data.loc[valuation_date]

print(f"Common valuation date: {valuation_date.date()}")
print(latest_market_data)

portfolio = pd.DataFrame(
    {
        "position_id": ["P001", "P002", "P003", "P004", "P005", "P006"],
        "asset_id": [
            "US_EQUITY",
            "EU_EQUITY",
            "US_GOV_BOND",
            "US_IG_CORP_BOND",
            "US_HIGH_YIELD_BOND",
            "GOLD",
        ],
        "asset_name": [
            "SPDR S&P 500 ETF",
            "iShares STOXX Europe 600 ETF",
            "iShares 7-10 Year Treasury Bond ETF",
            "iShares Investment Grade Corporate Bond ETF",
            "iShares High Yield Corporate Bond ETF",
            "SPDR Gold Shares",
        ],
        "asset_class": [
            "equity",
            "equity",
            "government_bond",
            "corporate_bond",
            "high_yield_bond",
            "commodity",
        ],
        "ticker": ["SPY", "EXSA.DE", "IEF", "LQD", "HYG", "GLD"],
        "target_weight": [0.30, 0.15, 0.20, 0.15, 0.10, 0.10],
        "currency": ["USD", "EUR", "USD", "USD", "USD", "USD"],
    }
)

print(portfolio)
print(f"Target weight total: {portfolio['target_weight'].sum():.2f}")

portfolio_value_usd = 100_000.0
portfolio["price"] = portfolio["ticker"].map(latest_market_data)
portfolio["fx_rate"] = 1.0
portfolio.loc[portfolio["currency"] == "EUR", "fx_rate"] = latest_market_data["EURUSD=X"]
portfolio["price_usd"] = portfolio["price"] * portfolio["fx_rate"]
portfolio["target_value_usd"] = portfolio_value_usd * portfolio["target_weight"]
portfolio["quantity"] = portfolio["target_value_usd"] / portfolio["price_usd"]

positions = portfolio[
    ["position_id", "asset_id", "asset_name", "asset_class", "quantity", "currency"]
]

positions.to_csv("data/processed/positions.csv", index=False)

print(
    portfolio[
        ["ticker", "target_weight", "price", "fx_rate", "price_usd", "target_value_usd", "quantity"]
    ]
)
