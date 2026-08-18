"""Generate deterministic sample market data for v0.1."""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OBSERVATION_COUNT = 251
END_DATE = "2025-12-31"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"

ASSETS = {
    "US_EQUITY": {"starting_price": 150.25, "currency": "USD"},
    "EU_EQUITY": {"starting_price": 120.40, "currency": "EUR"},
    "US_GOV_BOND": {"starting_price": 98.75, "currency": "USD"},
    "US_IG_CORP_BOND": {"starting_price": 102.30, "currency": "USD"},
    "US_HIGH_YIELD_BOND": {"starting_price": 95.60, "currency": "USD"},
    "GOLD": {"starting_price": 205.60, "currency": "USD"},
}

STARTING_FX_RATES = {
    "EUR": 1.04,
}

FACTOR_NAMES = (
    "US_EQUITY",
    "EU_EQUITY",
    "US_GOV_BOND",
    "US_IG_CORP_BOND",
    "US_HIGH_YIELD_BOND",
    "GOLD",
    "EUR_USD",
)

ANNUAL_DRIFT = np.array(
    [0.08, 0.06, 0.025, 0.035, 0.05, 0.04, 0.01],
    dtype=float,
)

DAILY_VOLATILITY = np.array(
    [0.010, 0.011, 0.003, 0.0045, 0.007, 0.008, 0.004],
    dtype=float,
)

# These illustrative parameters are used only to generate synthetic sample data.
# The Historical Simulation risk calculation does not use a correlation matrix.
CORRELATION_MATRIX = np.array(
    [
        [1.00, 0.75, -0.20, 0.20, 0.55, 0.10, 0.25],
        [0.75, 1.00, -0.15, 0.20, 0.50, 0.12, 0.40],
        [-0.20, -0.15, 1.00, 0.55, 0.10, 0.15, -0.10],
        [0.20, 0.20, 0.55, 1.00, 0.45, 0.10, 0.00],
        [0.55, 0.50, 0.10, 0.45, 1.00, 0.05, 0.10],
        [0.10, 0.12, 0.15, 0.10, 0.05, 1.00, 0.08],
        [0.25, 0.40, -0.10, 0.00, 0.10, 0.08, 1.00],
    ],
    dtype=float,
)


def generate_factor_returns() -> pd.DataFrame:
    """Generate 250 correlated synthetic daily factor returns."""

    rng = np.random.default_rng(SEED)
    daily_drift = ANNUAL_DRIFT / 252
    covariance_matrix = np.outer(DAILY_VOLATILITY, DAILY_VOLATILITY) * CORRELATION_MATRIX

    simulated_returns = rng.multivariate_normal(
        mean=daily_drift,
        cov=covariance_matrix,
        size=OBSERVATION_COUNT - 1,
    )

    return pd.DataFrame(
        simulated_returns,
        columns=FACTOR_NAMES,
    )


def generate_prices(factor_returns: pd.DataFrame) -> pd.DataFrame:
    """Convert synthetic asset returns into 251 daily price observations."""

    dates = pd.bdate_range(
        end=END_DATE,
        periods=OBSERVATION_COUNT,
    )
    records: list[dict[str, object]] = []

    for asset_id, attributes in ASSETS.items():
        starting_price = float(attributes["starting_price"])
        asset_returns = factor_returns[asset_id].to_numpy()

        prices = np.empty(OBSERVATION_COUNT)
        prices[0] = starting_price
        prices[1:] = starting_price * np.cumprod(1.0 + asset_returns)

        for date, price in zip(dates, prices, strict=True):
            records.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "asset_id": asset_id,
                    "price": round(float(price), 6),
                    "currency": attributes["currency"],
                }
            )

    return pd.DataFrame.from_records(records)


def generate_fx_rates(factor_returns: pd.DataFrame) -> pd.DataFrame:
    """Convert synthetic FX returns into 251 daily USD conversion rates."""

    dates = pd.bdate_range(
        end=END_DATE,
        periods=OBSERVATION_COUNT,
    )
    records: list[dict[str, object]] = []

    for currency, starting_rate in STARTING_FX_RATES.items():
        factor_name = f"{currency}_USD"
        currency_returns = factor_returns[factor_name].to_numpy()

        rates = np.empty(OBSERVATION_COUNT)
        rates[0] = starting_rate
        rates[1:] = starting_rate * np.cumprod(1.0 + currency_returns)

        for date, rate in zip(dates, rates, strict=True):
            records.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "currency": currency,
                    "usd_per_unit": round(float(rate), 6),
                }
            )

    return pd.DataFrame.from_records(records)


def validate_generated_data(
    prices: pd.DataFrame,
    fx_rates: pd.DataFrame,
) -> None:
    """Validate generated row counts, keys, and numeric values."""

    expected_price_rows = len(ASSETS) * OBSERVATION_COUNT
    expected_fx_rows = len(STARTING_FX_RATES) * OBSERVATION_COUNT

    if len(prices) != expected_price_rows:
        raise ValueError(f"Expected {expected_price_rows} price rows, got {len(prices)}.")

    if len(fx_rates) != expected_fx_rows:
        raise ValueError(f"Expected {expected_fx_rows} FX rows, got {len(fx_rates)}.")

    if prices.duplicated(["date", "asset_id"]).any():
        raise ValueError("Duplicate date and asset_id combinations found.")

    if fx_rates.duplicated(["date", "currency"]).any():
        raise ValueError("Duplicate date and currency combinations found.")

    if not np.isfinite(prices["price"]).all() or (prices["price"] <= 0).any():
        raise ValueError("Generated prices must be finite and greater than zero.")

    if not np.isfinite(fx_rates["usd_per_unit"]).all() or (fx_rates["usd_per_unit"] <= 0).any():
        raise ValueError("Generated FX rates must be finite and greater than zero.")


def main() -> None:
    """Generate, validate, and write the v0.1 sample market data."""

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    factor_returns = generate_factor_returns()
    prices = generate_prices(factor_returns)
    fx_rates = generate_fx_rates(factor_returns)

    validate_generated_data(prices, fx_rates)

    prices.to_csv(
        SAMPLE_DIR / "prices.csv",
        index=False,
    )
    fx_rates.to_csv(
        SAMPLE_DIR / "fx_rates.csv",
        index=False,
    )

    print(f"Wrote {len(prices):,} price rows to data/sample/prices.csv")
    print(f"Wrote {len(fx_rates):,} FX rows to data/sample/fx_rates.csv")


if __name__ == "__main__":
    main()
