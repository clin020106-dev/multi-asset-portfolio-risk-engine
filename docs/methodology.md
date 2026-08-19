# Case-Study Methodology

## Objective

The case study measures one-day USD market risk for a hypothetical multi-asset
portfolio and tests whether recent market conditions provide a modest early-warning
signal for next-day tail loss.

| Setting | Value |
| --- | --- |
| Base currency | USD |
| Data frequency | Daily |
| Risk horizon | One trading day |
| Historical Simulation window | 250 returns from 251 prices |
| Confidence levels | 95% and 99% |
| Predictive target | Next-day return below trailing 252-day 10th percentile |
| Walk-forward test years | 2020–2025 |

## 1. Portfolio Valuation

For asset `i`:

```text
Local market value(i) = quantity(i) × current local price(i)
USD market value(i) = local market value(i) × USD conversion rate(i)
```

USD positions use a conversion rate of 1.0. The European equity price is converted
using the same-date EUR/USD rate. Portfolio weights are calculated from current USD
market values.

## 2. Historical Simulation

Asset prices are converted to USD and aligned on common dates. Simple daily returns are
calculated as:

```text
return(i,t) = USD price(i,t) / USD price(i,t-1) - 1
```

Each aligned historical return vector is applied to current position values:

```text
scenario P&L(t) = sum[current USD value(i) × return(i,t)]
loss(t) = -scenario P&L(t)
```

The empirical nearest-rank convention is used:

```text
rank(c) = ceiling(c × number of scenarios)
VaR(c) = loss at rank(c)
ES(c) = mean loss from rank(c) through the worst scenario
```

The approach preserves observed cross-asset co-movement, but it gives equal weight to
old and recent scenarios and cannot create shocks that are absent from the window.

## 3. Predictive Target

For each prediction date `t`, the trailing 252-day 10th percentile is calculated from
portfolio returns available through `t`. The target is:

```text
high_loss(t) = 1 if portfolio return(t+1) < trailing threshold(t)
high_loss(t) = 0 otherwise
```

The threshold is adaptive, so the target represents an unusually poor return relative
to the recent market regime rather than a fixed dollar loss.

## 4. Predictive Features

### Market features

- 1-day portfolio return
- Mean 5-day and 20-day portfolio returns
- 5-day and 20-day portfolio volatility
- Mean 5-day U.S. equity return
- Mean 5-day U.S. government-bond return
- Mean 5-day gold return

### Interest-rate features

- Effective Federal Funds Rate
- 20-day federal-funds-rate change
- 5-day changes in 2-year and 10-year Treasury yields
- 10-year minus 2-year yield-curve slope
- 20-day yield-curve change

Interest-rate observations are shifted by one day before merging. No feature uses the
next-day return that defines the target.

## 5. Models

The 20-day volatility score is included as a simple non-ML benchmark. The statistical
baseline is class-balanced Logistic Regression with standardized features. The nonlinear
challenger is a deliberately small XGBoost classifier with 100 trees, maximum depth 3,
learning rate 0.05, and class weighting based on the training fold.

Hyperparameters remain fixed across all folds. The case study does not search many
parameter combinations and then report only the best result.

## 6. Walk-Forward Validation

Six calendar-year folds are evaluated:

```text
Train through 2019 → test 2020
Train through 2020 → test 2021
Train through 2021 → test 2022
Train through 2022 → test 2023
Train through 2023 → test 2024
Train through 2024 → test 2025
```

Training data expands through time, and each test year remains strictly later than its
training observations. Standardization and class weights are recalculated inside each
training fold.

## 7. Evaluation Metrics

Accuracy is not emphasized because roughly 10% of observations are high-loss events.
The primary ranking metrics are ROC-AUC and Average Precision. Precision, recall, F1,
and confusion-matrix counts describe behavior at the fixed 50% alert threshold.

Average Precision is compared with each year's event rate. A model must exceed that
baseline to demonstrate useful concentration of rare events.

## 8. Model Selection and Prediction

The market-only Logistic model is retained as the primary specification because it has
the highest mean Average Precision and mean F1 across the six walk-forward folds. The
XGBoost models remain challengers and provide nonlinear feature-importance analysis.

After retrospective evaluation, final models are refit on all labeled observations and
used to score the latest feature date. Because class weighting changes score
distributions, the outputs are called risk scores rather than calibrated probabilities.

## Limitations

- The portfolio and weights are hypothetical.
- ETFs are imperfect asset-class proxies.
- Historical Simulation omits events absent from the selected 250-day window.
- Tail estimates are based on few observations, especially at 99% confidence.
- Predictive observations are serially dependent and the sample is small.
- Model performance changes materially across years and regimes.
- The target is defined by a rolling sample percentile rather than an external outcome.
- Risk scores are not probability-calibrated.
- The analysis excludes derivatives, intraday risk, liquidity, costs, and market impact.

VaR, Expected Shortfall, and predictive scores are estimates, not guaranteed loss bounds.
