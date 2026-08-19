import pandas as pd

from market_risk_engine.risk.historical import expected_shortfall, losses, value_at_risk


def test_losses_negative_portfolio_pnl() -> None:
    pnl = pd.DataFrame(
        {
            "portfolio_pnl": [100.0, -250.0],
        }
    )
    result = losses(pnl)

    assert result["loss"].tolist() == [-100.0, 250.0]


def test_var_and_es() -> None:
    loss_data = pd.DataFrame({"loss": [10.0, 20.0, 30.0, 40.0, 50.0]})
    var = value_at_risk(loss_data, 0.80)
    es = expected_shortfall(loss_data, 0.80)

    assert var == 40.0
    assert es == 45.0
