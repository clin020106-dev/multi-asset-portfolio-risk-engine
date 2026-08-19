# Input Data Reference

Downloaded raw data are converted into four analysis-ready CSV files under
`data/processed/`. Processed data are reproducible through the download scripts and are
not required to be committed to source control.

## `positions.csv`

One row per hypothetical portfolio position.

| Field | Meaning |
| --- | --- |
| `position_id` | Unique position label |
| `asset_id` | Key used to join positions and prices |
| `asset_name` | Display name |
| `asset_class` | Reporting category |
| `quantity` | Units held |
| `currency` | Local price currency |

## `prices.csv`

Daily adjusted ETF closing prices in long format.

| Field | Meaning |
| --- | --- |
| `date` | Market observation date |
| `asset_id` | Position key |
| `price` | Positive adjusted closing price |
| `currency` | Price currency |

## `fx_rates.csv`

Daily EUR/USD conversion data.

| Field | Meaning |
| --- | --- |
| `date` | FX observation date |
| `currency` | Local currency, currently EUR |
| `usd_per_unit` | USD value of one local-currency unit |

USD rows are unnecessary because USD positions use a conversion rate of 1.0.

## `rates.csv`

Daily U.S. policy and Treasury-rate observations downloaded from FRED.

| Field | FRED Series | Meaning |
| --- | --- | --- |
| `date` | — | Observation date |
| `fed_funds_rate` | DFF | Effective Federal Funds Rate (%) |
| `treasury_2y_yield` | DGS2 | 2-year constant-maturity Treasury yield (%) |
| `treasury_10y_yield` | DGS10 | 10-year constant-maturity Treasury yield (%) |

Treasury observations are forward-filled across weekends and market holidays in the
download file. Predictive features are subsequently lagged one day before modeling.

## Asset Mapping

| Asset ID | Ticker | Exposure | Currency |
| --- | --- | --- | --- |
| `US_EQUITY` | SPY | U.S. large-cap equity | USD |
| `EU_EQUITY` | EXSA.DE | European equity | EUR |
| `US_GOV_BOND` | IEF | 7–10 year U.S. Treasury bonds | USD |
| `US_IG_CORP_BOND` | LQD | Investment-grade corporate bonds | USD |
| `US_HIGH_YIELD_BOND` | HYG | High-yield corporate bonds | USD |
| `GOLD` | GLD | Gold | USD |

## Analytical Assumptions

- All required portfolio assets have aligned price history.
- European prices have corresponding EUR/USD observations.
- Missing market values are never replaced with zero.
- Historical VaR uses the latest 251 common prices.
- Predictive modeling uses the longer common history and time-ordered evaluation.
