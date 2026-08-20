import pandas as pd

from market_risk_engine.risk.stress import (
    calculate_stress_scenario,
    run_stress_tests,
)


def test_calculate_stress_scenario() -> None:
    positions = pd.DataFrame(
        {"asset_id": ["ASSET_A", "ASSET_B"], "market_value_usd": [1000.0, 2000.0]}
    )

    shocks = {"ASSET_A": -0.10, "ASSET_B": 0.05}
    result = calculate_stress_scenario(positions, shocks, "Test Scenario")

    assert result["stress_pnl"].tolist() == [-100.0, 100.0]
    assert result["stress_loss"].tolist() == [100.0, -100.0]


def test_run_stress_tests() -> None:
    positions = pd.DataFrame(
        {
            "asset_id": [
                "US_EQUITY",
                "EU_EQUITY",
                "US_GOV_BOND",
                "US_IG_CORP_BOND",
                "US_HIGH_YIELD_BOND",
                "GOLD",
            ],
            "market_value_usd": [30000.0, 15000.0, 20000.0, 15000.0, 10000.0, 10000.0],
        }
    )

    stress_results, stress_summary = run_stress_tests(positions)

    losses = stress_summary.set_index("scenario")["stress_loss"]

    assert len(stress_results) == 18
    assert losses["Equity Selloff"] == 8000.0
    assert losses["Rates and Credit Shock"] == 8150.0
    assert losses["Broad Liquidity Crisis"] == 14300.0
