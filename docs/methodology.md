# Methodology

## Purpose

This document explains the methodology used in v0.1 of the Multi-Asset Portfolio Market Risk Engine. It describes the data inputs, assumptions, Historical Simulation process, Value at Risk (VaR) and Expected Shortfall (ES) calculations, outputs, and known limitations.

## Model Configuration

| Parameter | v0.1 Setting |
| --- | --- |
| Base currency | USD |
| Data frequency | Daily |
| Risk horizon | 1 trading day |
| Confidence levels | 95% and 99% |
| Historical observation window | 250 trading days |
| Method | Historical Simulation |
| Risk measures | Value at Risk (VaR) and Expected Shortfall (ES) |
| Data source | Project-provided sample data |

## Input Data

v0.1 uses project-provided sample data instead of live market data or external data-provider connections.

The calculation requires the following inputs:

- Portfolio positions, including an asset identifier, asset class, position size, and position currency.
- Daily market data for each asset or relevant market risk factors.
- Daily foreign exchange rates for converting non-USD positions into USD.

Before calculation, the input data should:

- Be ordered by date from oldest to newest.
- Contain no duplicate dates for the same asset or risk factor.
- Provide at least 251 valid daily observations to calculate 250 daily changes.
- Have missing or invalid values identified before risk measures are calculated.

## Calculation Workflow

The v0.1 risk calculation follows these steps:

1. Load and validate the portfolio and daily market data.
2. Convert non-USD positions and market values into USD.
3. Calculate daily changes in asset prices or relevant market risk factors.
4. Select the most recent 250 valid daily changes.
5. Apply each historical daily change to the current portfolio to create 250 historical scenarios.
6. Revalue the portfolio under each scenario and calculate the corresponding one-day profit and loss (P&L).
7. Convert negative P&L values into positive loss amounts and rank the losses from smallest to largest.
8. Calculate VaR and ES at the 95% and 99% confidence levels.

## Base Currency and Portfolio Valuation

All position values and risk results are expressed in USD. A position already denominated in USD requires no currency conversion.

For a non-USD position, its USD value is calculated as:

```text
V_USD(i,t) = V_local(i,t) × FX(i,t)
```

where:

- `V_local(i,t)` is the value of position `i` in its local currency on date `t`.
- `FX(i,t)` is the number of USD per unit of the local currency on date `t`.
- `V_USD(i,t)` is the resulting position value in USD.

The total portfolio value is calculated as:

```text
V_portfolio(t) = sum of V_USD(i,t) across all positions
```

## Daily Return Calculation

Historical Simulation uses observed daily market changes. In v0.1, each asset's daily simple return is calculated from its USD-denominated price or value:

```text
r(i,t) = [P_USD(i,t) / P_USD(i,t-1)] - 1
```

where:

- `r(i,t)` is the daily return of asset `i` on date `t`.
- `P_USD(i,t)` is the USD-denominated price or value of asset `i` on date `t`.
- `P_USD(i,t-1)` is the corresponding price or value on the previous valid trading date.

A positive return represents a gain, while a negative return represents a loss. Because one return requires two consecutive observations, 251 valid price observations are required to produce 250 daily returns.

Dates must be aligned across assets before portfolio scenarios are created. Missing observations must not be automatically replaced with zero returns.

## Historical Scenario Generation

Each of the 250 historical dates represents one joint market scenario. The returns observed across all assets on the same date are kept together and applied simultaneously to the current portfolio.

For each asset `i` under historical scenario `s`, the scenario value is calculated as:

```text
V_scenario(i,s) = V_current(i) × [1 + r(i,s)]
```

where:

- `V_current(i)` is the current USD value of asset `i`.
- `r(i,s)` is the historical daily return of asset `i` in scenario `s`.
- `V_scenario(i,s)` is the simulated USD value of asset `i` after applying that return.

Keeping same-date returns together preserves the historical co-movement between assets. The method produces 250 portfolio scenarios without assuming that returns follow a normal distribution.

## Scenario Profit and Loss

The simulated portfolio value under scenario `s` is the sum of all simulated position values:

```text
V_portfolio(s) = sum of V_scenario(i,s) across all positions
```

The one-day scenario profit and loss is calculated as:

```text
PnL(s) = V_portfolio(s) - V_current_portfolio
```

For risk reporting, P&L is converted into a loss amount:

```text
Loss(s) = -PnL(s)
```

Under this sign convention:

- A positive `PnL(s)` represents a portfolio gain.
- A negative `PnL(s)` represents a portfolio loss.
- A positive `Loss(s)` represents a loss.
- A negative `Loss(s)` represents a gain.

The 250 loss values are sorted from smallest to largest before VaR and ES are calculated.

## Value at Risk (VaR)

Value at Risk estimates a loss threshold at a specified confidence level over the one-day risk horizon.

Let the 250 scenario losses be sorted from smallest to largest:

```text
L(1) ≤ L(2) ≤ ... ≤ L(N)
```

where `N = 250`. v0.1 uses the empirical nearest-rank method without interpolation:

```text
Rank(c) = ceiling(c × N)
VaR(c) = L[Rank(c)]
```

where `c` is the confidence level.

For 250 scenarios:

- The 95% VaR is the loss at rank `ceiling(0.95 × 250) = 238`.
- The 99% VaR is the loss at rank `ceiling(0.99 × 250) = 248`.

For example, a one-day 95% VaR of USD 100,000 means that, based on the historical simulation, the portfolio loss is estimated not to exceed USD 100,000 on approximately 95% of trading days. VaR does not describe how large losses may become after the threshold is exceeded.

## Expected Shortfall (ES)

Expected Shortfall estimates the average loss in the tail of the loss distribution at a specified confidence level. It describes the severity of losses when the VaR threshold is reached or exceeded.

Using the same nearest-rank convention:

```text
k = ceiling(c × N)
ES(c) = average of L(k), L(k+1), ..., L(N)
```

For 250 scenarios:

- The 95% ES is the average of losses at ranks 238 through 250, using 13 tail observations.
- The 99% ES is the average of losses at ranks 248 through 250, using 3 tail observations.

Expected Shortfall is designed to provide information about losses beyond the VaR threshold. Under the defined convention, ES should be greater than or equal to the corresponding VaR when reported as a positive loss amount.

Because the 99% ES uses only three observations in a 250-day window, it can be sensitive to individual extreme market moves. This is a known limitation of the v0.1 configuration.

## Risk Outputs

Each successful v0.1 calculation should report:

- Valuation date.
- Current portfolio value in USD.
- Risk horizon of one trading day.
- Historical observation window and number of valid scenarios.
- 95% one-day VaR in USD.
- 99% one-day VaR in USD.
- 95% one-day ES in USD.
- 99% one-day ES in USD.
- The methodology and configuration used for the calculation.
- Data-quality warnings or calculation limitations, when applicable.

VaR and ES are reported as positive USD loss amounts. The output should clearly identify the valuation date so that results from different calculation dates are not confused.

## Key Assumptions

The v0.1 methodology relies on the following assumptions:

- Portfolio positions remain unchanged during the one-day risk horizon.
- Historical observations are relevant for estimating current market risk.
- Each of the 250 historical scenarios receives equal weight.
- Same-date returns across assets preserve the historical dependence between positions.
- Daily prices, position data, and foreign exchange rates are accurate and aligned by date.
- Historical asset returns can be applied proportionally to current position values.
- No trades, deposits, withdrawals, fees, taxes, or other cash flows occur during the risk horizon.
- The sample portfolio does not require advanced nonlinear derivatives pricing.


## Limitations

The v0.1 methodology has the following limitations:

- Historical Simulation is backward-looking and cannot represent market events that are absent from the observation window.
- Results can change materially when extreme observations enter or leave the 250-day rolling window.
- Equal weighting does not give greater importance to more recent market conditions.
- The 99% ES estimate is based on only three tail observations and may be unstable.
- Daily data does not capture intraday price movements or liquidity stress.
- A one-day risk horizon does not measure losses over longer holding periods.
- Proportional revaluation does not capture nonlinear behavior from advanced derivatives.
- The calculation does not include transaction costs, bid-ask spreads, market impact, or forced-liquidation effects.
- Sample data may not reflect the quality, completeness, or complexity of production market data.
- v0.1 does not include backtesting, stress testing, or independent model validation.

VaR and ES should therefore be interpreted as model-based estimates rather than guarantees of maximum possible loss.

## Data Validation

Before calculating risk measures, v0.1 should verify that:

- All required portfolio and market-data fields are present.
- Dates are valid, unique within each series, and ordered consistently.
- Each required series contains enough observations to produce 250 valid daily returns.
- Prices and foreign exchange rates are positive numeric values.
- Position sizes and currencies are valid and clearly identified.
- Missing, infinite, and non-numeric values are detected.
- Market-data dates are aligned across assets before joint scenarios are created.
- The final scenario set contains exactly 250 valid observations.

Invalid data should produce a clear error or warning. The engine should not silently replace missing prices with zero or continue with an incomplete scenario set.

## Reproducibility

Historical Simulation in v0.1 is deterministic and does not use random sampling. The same portfolio, market data, valuation date, and configuration should therefore produce the same VaR and ES results.

To make a calculation reproducible, the output or calculation record should identify:

- The valuation date.
- The input portfolio and market-data versions.
- The 250 historical dates included in the observation window.
- The base currency and risk horizon.
- The confidence levels.
- The VaR nearest-rank convention.
- The ES tail-selection convention.
- Any data-quality warnings or excluded observations.

Any change to the input data, observation window, calculation convention, or portfolio positions may change the reported risk measures.
