import pandas as pd
import pytest

from market_risk_engine.portfolio.valuation import (
    calculate_usd_market_values,
    portfolio_weights,
)


def test_usd_market_values_and_weights() -> None:
    positions = pd.DataFrame(
        {
            "local_market_value": [100.0, 200.0],
            "usd_per_unit": [1.0, 1.1],
        }
    )

    result = calculate_usd_market_values(positions)
    result = portfolio_weights(result)

    assert result["market_value_usd"].tolist() == pytest.approx([100.0, 220.0])
    assert result["portfolio_weight"].sum() == pytest.approx(1.0)
