"""Historical Simulation calculations."""

import math

import pandas as pd


def convert_prices_to_usd(
    prices: pd.DataFrame,
    fx_rates: pd.DataFrame,
) -> pd.DataFrame:
    """Convert every historical asset price to USD."""
    df = prices.merge(
        fx_rates,
        on=["date", "currency"],
        how="left",
    )
    df.loc[df["currency"] == "USD", "usd_per_unit"] = 1.0
    df["price_usd"] = df["price"] * df["usd_per_unit"]

    return df


def pivot_usd_prices(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    """Create an aligned date-by-asset table of USD prices."""
    df = prices.pivot(
        index="date",
        columns="asset_id",
        values="price_usd",
    )

    df = df.dropna()
    df = df.sort_index()
    df = df.tail(251)

    return df


def daily_return(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate daily simple returns."""
    df = prices.pct_change()
    df = df.dropna()

    return df


def historical_pnl(
    returns: pd.DataFrame,
    positions: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate asset and portfolio P&L for each historical scenario."""
    market_values = positions.set_index("asset_id")["market_value_usd"]

    df = returns * market_values
    df["portfolio_pnl"] = df.sum(axis=1)

    return df


def losses(
    pnl: pd.DataFrame,
) -> pd.DataFrame:
    """Express portfolio P&L as positive loss amounts."""
    df = pnl.copy()
    df["loss"] = -df["portfolio_pnl"]

    return df


def value_at_risk(
    loss_data: pd.DataFrame,
    confidence: float,
) -> float:
    """Calculate nearest-rank Historical Simulation VaR."""
    sorted_losses = loss_data["loss"].sort_values().reset_index(drop=True)
    rank = math.ceil(confidence * len(sorted_losses))
    var = sorted_losses.iloc[rank - 1]

    return float(var)


def expected_shortfall(
    loss_data: pd.DataFrame,
    confidence: float,
) -> float:
    """Calculate the mean loss from the VaR rank through the worst loss."""
    sorted_losses = loss_data["loss"].sort_values().reset_index(drop=True)
    rank = math.ceil(confidence * len(sorted_losses))
    tail_losses = sorted_losses.iloc[rank - 1 :]
    es = tail_losses.mean()

    return float(es)
