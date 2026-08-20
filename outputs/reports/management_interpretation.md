# Management Interpretation

## Decision Summary

The USD 100,000 hypothetical portfolio has meaningful but manageable one-day market
risk under ordinary historical conditions. The 95% Historical Simulation VaR is USD
625.91, while the 95% Expected Shortfall is USD 1,139.60. The difference shows that once
the portfolio moves beyond the VaR threshold, losses become substantially more severe.

Management should use VaR as a frequency-based threshold, Expected Shortfall as the
better measure of tail severity, and worst-scenario contribution as the guide to where
risk reduction would be most effective.

## Tail-Risk Findings

| Measure | USD | Portfolio % |
| --- | ---: | ---: |
| 95% VaR | 625.91 | 0.63% |
| 95% Expected Shortfall | 1,139.60 | 1.14% |
| 99% VaR | 1,578.95 | 1.58% |
| 99% Expected Shortfall | 1,997.09 | 2.00% |
| Worst observed scenario | 2,705.90 | 2.71% |

The worst scenario is more than four times the 95% VaR. This is not a contradiction:
VaR is a percentile threshold, not a maximum-loss estimate. Expected Shortfall and
explicit stress scenarios should therefore accompany any VaR limit discussion.

## Concentration and Diversification

The worst scenario occurred on 4 April 2025. U.S. equity contributed a USD 1,756 loss
and European equity contributed a USD 613 loss. Together, the two equity exposures
generated approximately 87.5% of the total loss.

U.S. government bonds offset approximately USD 56, but the benefit was small relative
to the equity decline. Gold lost approximately USD 234, demonstrating that an asset
commonly treated as a diversifier may still decline during a specific liquidity or
risk-off event. Diversification should be evaluated by scenario rather than assumed from
asset labels.

## Stress-Test Findings

| Scenario | Portfolio Loss | Portfolio % |
| --- | ---: | ---: |
| Equity Selloff | USD 8,000 | 8.00% |
| Rates and Credit Shock | USD 8,150 | 8.15% |
| Broad Liquidity Crisis | USD 14,300 | 14.30% |

The Broad Liquidity Crisis produces the most severe loss because all major asset classes
decline at the same time. The portfolio loses USD 14,300, substantially more than the
USD 2,706 worst loss observed in the Historical Simulation window.

The Equity Selloff scenario shows some diversification benefit from government bonds and
gold. However, that protection disappears in the Broad Liquidity Crisis. This means the
portfolio's apparent diversification depends on the relationships between asset classes
remaining stable during periods of stress.

These scenarios are hypothetical and are not forecasts. They do not estimate how likely
each event is to occur. Their purpose is to show the financial impact if the assumed
market shocks occur.

## Predictive Early-Warning Models

Six annual walk-forward tests compare a volatility benchmark, Logistic Regression, and
XGBoost with and without U.S. interest-rate features. The market-only Logistic model has
the strongest average rare-event performance:

| Metric | Six-Year Mean |
| --- | ---: |
| ROC-AUC | 0.571 |
| Average Precision | 0.151 |
| Precision at 50% threshold | 0.135 |
| Recall at 50% threshold | 0.448 |
| F1 score | 0.204 |
| High-loss event rate | 0.105 |

Average Precision is 1.44 times the unconditional event-rate baseline, indicating modest
risk concentration. However, mean precision of 13.5% implies a large number of false
alerts, and performance varies considerably across test years. The model is not suitable
for automated trading, position liquidation, or hard risk limits.

The appropriate use is as a soft monitoring signal. A rising score could prompt review
of current exposures, scenario analysis, or more frequent risk reporting. It should not
replace VaR, Expected Shortfall, or human judgment.

The standardized Logistic coefficients indicate that weaker recent portfolio returns
and higher recent volatility are associated with a higher next-day risk score. Other
asset coefficients are conditional on correlated portfolio features and should not be
read as causal effects in isolation.

## Interest-Rate Experiment

Federal-funds-rate, Treasury-yield-change, and yield-curve features have clear economic
relevance to the bond, credit, equity, and gold exposures. They nevertheless reduce
average walk-forward performance in both Logistic Regression and XGBoost.

This result suggests regime dependency rather than proving that rates are irrelevant.
The relationship between policy rates and next-day portfolio loss changes with inflation,
growth expectations, and market positioning. Management should not assume that adding
more macro variables automatically creates a more robust forecasting model.

## Latest Score

On 30 December 2025, the primary market-only Logistic model produces a high-loss risk
score of 41.0%, below the fixed 50% alert threshold. The model therefore assigns the
normal-risk class. Because class weighting is used and calibration has not been
performed, 41.0% is a relative score rather than a literal event probability.

## Recommended Actions

1. Retain Historical VaR and Expected Shortfall as the primary daily risk measures.
2. Monitor equity contribution because equity drives the largest observed loss.
3. Use the predictive score only as a secondary review trigger.
4. Review results across regimes rather than relying on a single holdout year.
5. Use the stress scenarios to evaluate whether an 8% to 14% portfolio loss is within
   management's risk tolerance and available loss-absorbing capacity.
6. Calibrate probabilities and define alert costs before presenting model scores as
   decision probabilities.

The results are educational and based on a hypothetical portfolio. They do not constitute
investment advice or a production risk limit recommendation.
