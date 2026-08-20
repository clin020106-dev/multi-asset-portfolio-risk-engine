
from pathlib import Path

import pandas as pd

_POSITIONS_COLUMNS = ("position_id","asset_id", "asset_name", "asset_class", "quantity", "currency")
_PRICES_COLUMNS = ("date", "asset_id", "price", "currency")
_FX_RATES_COLUMNS = ("date", "currency", "usd_per_unit")
_INTEREST_RATE_COLUMNS = ("date", "fed_funds_rate", "treasury_2y_yield", "treasury_10y_yield",)


def _load_csv(path: str | Path, required_columns: tuple[str, ...]) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding="utf-8")
    missing_columns = [column for column in required_columns if column not in frame.columns]

    if missing_columns:
        raise ValueError(f"{path}: missing required columns {missing_columns}.")

    if frame.loc[:, list(required_columns)].isna().any().any():
        raise ValueError(f"{path}: required fields contain missing values.")

    return frame


def _parse_dates(frame: pd.DataFrame, path: str | Path) -> None:
    try:
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: date contains an invalid value.") from exc


def _parse_numeric(frame: pd.DataFrame, column: str, path: str | Path) -> None:
    try:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: {column} must be numeric.") from exc


def load_positions(path: str | Path) -> pd.DataFrame:
    frame = _load_csv(path, _POSITIONS_COLUMNS)
    _parse_numeric(frame, "quantity", path)
    return frame


def load_prices(path: str | Path) -> pd.DataFrame:
    frame = _load_csv(path, _PRICES_COLUMNS)
    _parse_dates(frame, path)
    _parse_numeric(frame, "price", path)

    if (frame["price"] <= 0).any():
        raise ValueError(f"{path}: price must be greater than zero.")

    return frame


def load_fx_rates(path: str | Path) -> pd.DataFrame:
    frame = _load_csv(path, _FX_RATES_COLUMNS)
    _parse_dates(frame, path)
    _parse_numeric(frame, "usd_per_unit", path)

    if (frame["usd_per_unit"] <= 0).any():
        raise ValueError(f"{path}: usd_per_unit must be greater than zero.")

    return frame


def load_interest_rates(path: str | Path) -> pd.DataFrame:
    frame = _load_csv(path, _INTEREST_RATE_COLUMNS)

    _parse_dates(frame, path)
    _parse_numeric(frame, "fed_funds_rate", path)
    _parse_numeric(frame, "treasury_2y_yield", path)
    _parse_numeric(frame, "treasury_10y_yield", path)

    return frame
