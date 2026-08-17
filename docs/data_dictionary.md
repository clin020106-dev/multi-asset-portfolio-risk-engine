# Data Dictionary

## Purpose

This document defines the input data structure, required fields, data types, validation rules, and sample-data conventions for v0.1 of the Multi-Asset Portfolio Market Risk Engine.

## Input Files

v0.1 uses three CSV input files stored in `data/sample/`.

| File | Purpose |
| --- | --- |
| `positions.csv` | Defines the portfolio positions included in the risk calculation. |
| `prices.csv` | Provides daily historical closing prices for each asset. |
| `fx_rates.csv` | Provides daily foreign exchange rates used to convert non-USD values into USD. |

## `positions.csv`

Each row represents one portfolio position as of the valuation date.

| Field | Data Type | Required | Description |
| --- | --- | --- | --- |
| `position_id` | String | Yes | Unique identifier for the portfolio position. |
| `asset_id` | String | Yes | Asset identifier that matches the corresponding records in `prices.csv`. |
| `asset_name` | String | Yes | Human-readable asset name used in reports. |
| `asset_class` | String | Yes | Asset-class classification used for grouping and reporting. |
| `quantity` | Number | Yes | Number of units held. Positive values represent long positions and negative values represent short positions. |
| `currency` | String | Yes | Three-letter ISO currency code for the asset price, such as `USD`, `EUR`, or `JPY`. |

## `prices.csv`

Each row represents the daily closing price of one asset on one trading date.

| Field | Data Type | Required | Description |
| --- | --- | --- | --- |
| `date` | Date | Yes | Trading date in `YYYY-MM-DD` format. |
| `asset_id` | String | Yes | Asset identifier that matches an `asset_id` in `positions.csv`. |
| `price` | Number | Yes | Positive daily closing price in the specified currency. Prices should be adjusted for corporate actions when applicable. |
| `currency` | String | Yes | Three-letter ISO currency code in which the price is denominated. |

## `fx_rates.csv`

Each row represents the USD conversion rate for one non-USD currency on one trading date.

| Field | Data Type | Required | Description |
| --- | --- | --- | --- |
| `date` | Date | Yes | Trading date in `YYYY-MM-DD` format. |
| `currency` | String | Yes | Three-letter ISO code for the non-USD currency being converted. |
| `usd_per_unit` | Number | Yes | Positive number of USD per one unit of the specified currency. |

For example, if one EUR equals USD 1.10, `currency` is `EUR` and `usd_per_unit` is `1.10`. USD-denominated assets do not require an FX record because their conversion rate is implicitly `1.0`.

## Common Validation Rules

All input files must:

- Use UTF-8 encoding and comma-separated values.
- Include one header row with field names that exactly match this data dictionary.
- Contain no missing values in required fields.
- Contain no leading or trailing whitespace in string fields.
- Use uppercase three-letter ISO currency codes.
- Use ISO 8601 dates in `YYYY-MM-DD` format.
- Contain finite numeric values without currency symbols or thousands separators.

### Position Validation

For `positions.csv`:

- Each `position_id` must be unique and non-empty.
- Each `asset_id` must have corresponding price records in `prices.csv`.
- Each `asset_name` and `asset_class` must be non-empty.
- Each `quantity` must be finite and non-zero.
- The `currency` for an asset must match its currency in `prices.csv`.
- Positive quantities represent long positions, and negative quantities represent short positions.

### Price Validation

For `prices.csv`:

- Each combination of `date` and `asset_id` must be unique.
- Records for each asset must be ordered from oldest to newest by date.
- Each `price` must be finite and greater than zero.
- Each asset must have at least 251 valid price observations to produce 250 daily returns.
- Each asset must use one consistent `currency` across all dates.
- Missing prices must not be replaced with zero.

### FX Rate Validation

For `fx_rates.csv`:

- Each combination of `date` and `currency` must be unique.
- Records for each currency must be ordered from oldest to newest by date.
- Each `usd_per_unit` value must be finite and greater than zero.
- Every non-USD currency used in `positions.csv` and `prices.csv` must have an FX rate for every required price date.
- Missing FX rates must not be replaced with zero or silently forward-filled.
- USD records should be omitted because the USD conversion rate is implicitly `1.0`.

## Cross-File Consistency

Before risk measures are calculated:

- Every `asset_id` in `positions.csv` must have corresponding records in `prices.csv`.
- The currency assigned to each asset must match between `positions.csv` and `prices.csv`.
- Each non-USD price must be converted using the same-date `usd_per_unit` value from `fx_rates.csv`.
- Price dates must be aligned across all portfolio assets before joint historical scenarios are created.
- The most recent 251 aligned valid dates are used to produce 250 daily portfolio-return scenarios.
- The most recent aligned date is the valuation date for the v0.1 sample calculation.

## Illustrative Records

The following rows illustrate the required structure. They are not the complete v0.1 sample dataset.

### `positions.csv`

```csv
position_id,asset_id,asset_name,asset_class,quantity,currency
P001,US_EQUITY,US Equity Index,equity,100,USD
P002,EU_EQUITY,European Equity Index,equity,80,EUR
P003,US_BOND,US Treasury Bond,fixed_income,50,USD
P004,GOLD,Gold Commodity,commodity,25,USD
```

### `prices.csv`

```csv
date,asset_id,price,currency
2025-01-02,US_EQUITY,150.25,USD
2025-01-02,EU_EQUITY,120.40,EUR
2025-01-02,US_BOND,98.75,USD
2025-01-02,GOLD,205.60,USD
```

### `fx_rates.csv`

```csv
date,currency,usd_per_unit
2025-01-02,EUR,1.04
```

## Error Handling

Invalid required input data must stop the risk calculation and produce a clear error message. When possible, the message should identify the file, field, row, and reason for failure.

Warnings may be used for non-blocking issues that do not change the validity of the 250-scenario calculation. The engine must not continue when required data is missing, currencies are inconsistent, numeric values are invalid, or fewer than 251 aligned valid dates are available.

## Sample Data Reproducibility

The v0.1 sample input files are project-provided, version-controlled datasets intended for demonstration and testing. They do not represent live market data or investment recommendations.

A calculation record should identify the input-file versions, valuation date, and 251 aligned dates used to create the 250 daily return scenarios. Unchanged input files and configuration must produce identical validated inputs and risk results.
