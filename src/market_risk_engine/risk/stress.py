import pandas as pd

EQUITY_SELLOFF = {
    "US_EQUITY": -0.15,
    "EU_EQUITY": -0.20,
    "US_GOV_BOND": 0.03,
    "US_IG_CORP_BOND": -0.04,
    "US_HIGH_YIELD_BOND": -0.10,
    "GOLD": 0.05,
}
RATES_AND_CREDIT_SHOCK = {
    "US_EQUITY": -0.08,
    "EU_EQUITY": -0.10,
    "US_GOV_BOND": -0.07,
    "US_IG_CORP_BOND": -0.09,
    "US_HIGH_YIELD_BOND": -0.12,
    "GOLD": -0.03,
}
BROAD_LIQUIDITY_CRISIS = {
    "US_EQUITY": -0.20,
    "EU_EQUITY": -0.22,
    "US_GOV_BOND": -0.03,
    "US_IG_CORP_BOND": -0.12,
    "US_HIGH_YIELD_BOND": -0.18,
    "GOLD": -0.08,
}


def calculate_stress_scenario(
    positions: pd.DataFrame, shocks: dict[str, float], scenario_name: str
) -> pd.DataFrame:
    df = positions.copy()
    df["scenario"] = scenario_name
    df["stress_return"] = df["asset_id"].map(shocks)
    df["stress_pnl"] = df["market_value_usd"] * df["stress_return"]
    df["stress_loss"] = -df["stress_pnl"]

    return df


def run_stress_tests(positions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    portfolio_value = positions["market_value_usd"].sum()

    equity_selloff = calculate_stress_scenario(positions, EQUITY_SELLOFF, "Equity Selloff")
    rates_and_credit = calculate_stress_scenario(
        positions, RATES_AND_CREDIT_SHOCK, "Rates and Credit Shock"
    )
    broad_liquidity_crisis = calculate_stress_scenario(
        positions, BROAD_LIQUIDITY_CRISIS, "Broad Liquidity Crisis"
    )
    stress_results = pd.concat(
        [equity_selloff, rates_and_credit, broad_liquidity_crisis],
        ignore_index=True,
    )
    stress_summary = stress_results.groupby("scenario", as_index=False)["stress_loss"].sum()
    stress_summary["loss_percent"] = stress_summary["stress_loss"] / portfolio_value

    return stress_results, stress_summary
