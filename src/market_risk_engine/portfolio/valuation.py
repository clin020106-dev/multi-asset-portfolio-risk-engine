"""Portfolio valuation functions for the market-risk case study."""

import pandas as pd


def get_latest_prices(
    prices: pd.DataFrame,
) -> tuple[pd.Timestamp, pd.DataFrame]:
    """Get each asset's price on the latest common date."""
    price_table = prices.pivot(
        index="date",
        columns="asset_id",
        values="price",
    )

    valuation_date = price_table.dropna().index.max()

    df = prices.loc[
        prices["date"] == valuation_date,
        ["asset_id", "price", "currency"],
    ].copy()

    return valuation_date, df


def merge_positions_with_prices(
    positions: pd.DataFrame,
    latest_prices: pd.DataFrame,
) -> pd.DataFrame:
    """Merge portfolio positions with their latest prices."""
    df = positions.merge(
        latest_prices,
        on=["asset_id", "currency"],
        how="left",
    )

    return df


def calculate_local_market_values(
    positions: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate each position's market value in local currency."""
    df = positions.copy()
    df["local_market_value"] = df["quantity"] * df["price"]

    return df


def add_fx_rates(
    positions: pd.DataFrame,
    fx_rates: pd.DataFrame,
    valuation_date: pd.Timestamp,
) -> pd.DataFrame:
    """Add valuation-date FX rates to the positions."""
    latest_fx = fx_rates.loc[
        fx_rates["date"] == valuation_date,
        ["currency", "usd_per_unit"],
    ].copy()

    df = positions.merge(latest_fx, on="currency", how="left")
    df.loc[df["currency"] == "USD", "usd_per_unit"] = 1.0

    return df


def calculate_usd_market_values(
    positions: pd.DataFrame,
) -> pd.DataFrame:
    """Convert local market values to USD."""
    df = positions.copy()
    df["market_value_usd"] = df["local_market_value"] * df["usd_per_unit"]

    return df


def portfolio_weights(
    positions: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate each position's share of total portfolio value."""
    df = positions.copy()
    total_value = df["market_value_usd"].sum()
    df["portfolio_weight"] = df["market_value_usd"] / total_value

    return df
