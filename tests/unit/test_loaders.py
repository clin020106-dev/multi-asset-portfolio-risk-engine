from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from market_risk_engine.data.loaders import (
    load_fx_rates,
    load_interest_rates,
    load_positions,
    load_prices,
)


def test_load_positions_parses_quantity(tmp_path: Path) -> None:
    path = tmp_path / "positions.csv"
    path.write_text(
        "position_id,asset_id,asset_name,asset_class,quantity,currency\n"
        "P001,US_EQUITY,US Equity Index,equity,100,USD\n",
        encoding="utf-8",
    )

    result = load_positions(path)

    assert result.loc[0, "quantity"] == 100


def test_load_prices_parses_date_and_price(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    path.write_text(
        "date,asset_id,price,currency\n2025-01-02,US_EQUITY,150.25,USD\n",
        encoding="utf-8",
    )

    result = load_prices(path)

    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result.loc[0, "price"] == 150.25


def test_load_fx_rates_parses_date_and_rate(tmp_path: Path) -> None:
    path = tmp_path / "fx_rates.csv"
    path.write_text(
        "date,currency,usd_per_unit\n2025-01-02,EUR,1.04\n",
        encoding="utf-8",
    )

    result = load_fx_rates(path)

    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result.loc[0, "usd_per_unit"] == 1.04


def test_load_interest_rates_parses_date_and_rates(tmp_path: Path) -> None:
    path = tmp_path / "rates.csv"
    path.write_text(
        "date,fed_funds_rate,treasury_2y_yield,treasury_10y_yield\n2025-01-02,4.33,4.25,4.57\n",
        encoding="utf-8",
    )

    result = load_interest_rates(path)

    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result.loc[0, "fed_funds_rate"] == 4.33
    assert result.loc[0, "treasury_10y_yield"] == 4.57


@pytest.mark.parametrize(
    ("loader", "contents"),
    [
        (
            load_positions,
            "position_id,asset_id,asset_name,asset_class,quantity\n"
            "P001,US_EQUITY,US Equity Index,equity,100\n",
        ),
        (load_prices, "date,asset_id,price\n2025-01-02,US_EQUITY,150.25\n"),
        (load_fx_rates, "date,currency\n2025-01-02,EUR\n"),
        (
            load_interest_rates,
            "date,fed_funds_rate,treasury_2y_yield\n2025-01-02,4.33,4.25\n",
        ),
    ],
)
def test_loaders_reject_missing_required_columns(
    tmp_path: Path,
    loader: Callable[[Path], pd.DataFrame],
    contents: str,
) -> None:
    path = tmp_path / "input.csv"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        loader(path)


def test_load_prices_rejects_non_positive_prices(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    path.write_text(
        "date,asset_id,price,currency\n2025-01-02,US_EQUITY,0,USD\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="greater than zero"):
        load_prices(path)


def test_load_fx_rates_rejects_non_positive_rates(tmp_path: Path) -> None:
    path = tmp_path / "fx_rates.csv"
    path.write_text(
        "date,currency,usd_per_unit\n2025-01-02,EUR,-1.04\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="greater than zero"):
        load_fx_rates(path)
