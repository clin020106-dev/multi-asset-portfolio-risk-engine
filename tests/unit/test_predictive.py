import pandas as pd
import pytest

from market_risk_engine.risk.predictive import (
    add_interest_rate_features,
    classification_metrics,
)


def test_classification_metrics_reports_confusion_matrix_counts() -> None:
    actual = pd.Series([0, 0, 1, 1])
    probability = pd.Series([0.10, 0.80, 0.40, 0.90])

    result = classification_metrics(actual, probability)

    assert result["roc_auc"] == pytest.approx(0.75)
    assert result["average_precision"] == pytest.approx(5 / 6)
    assert result["precision"] == pytest.approx(0.50)
    assert result["recall"] == pytest.approx(0.50)
    assert result["true_negative"] == 1
    assert result["false_positive"] == 1
    assert result["false_negative"] == 1
    assert result["true_positive"] == 1


def test_interest_rate_features_use_previous_day_rates() -> None:
    dates = pd.date_range("2025-01-01", periods=30, freq="D")
    data = pd.DataFrame(
        {"portfolio_return": [0.001] * 30},
        index=dates,
    )
    data.index.name = "date"
    rates = pd.DataFrame(
        {
            "date": dates,
            "fed_funds_rate": range(30),
            "treasury_2y_yield": range(100, 130),
            "treasury_10y_yield": range(200, 230),
        }
    )

    result = add_interest_rate_features(data, rates)
    first_date = result.index.min()

    assert result.loc[first_date, "fed_funds_rate"] == 20
    assert result.loc[first_date, "treasury_2y_change_5d"] == 5
    assert result.loc[first_date, "yield_curve"] == 100
