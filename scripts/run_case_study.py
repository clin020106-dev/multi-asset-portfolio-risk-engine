import matplotlib.pyplot as plt
import pandas as pd

from market_risk_engine.data.loaders import load_fx_rates, load_positions, load_prices
from market_risk_engine.portfolio.valuation import (
    add_fx_rates,
    calculate_local_market_values,
    calculate_usd_market_values,
    get_latest_prices,
    merge_positions_with_prices,
    portfolio_weights,
)
from market_risk_engine.risk.historical import (
    convert_prices_to_usd,
    daily_return,
    expected_shortfall,
    historical_pnl,
    losses,
    pivot_usd_prices,
    value_at_risk,
)
from market_risk_engine.risk.stress import run_stress_tests

positions = load_positions("data/processed/positions.csv")
prices = load_prices("data/processed/prices.csv")
fx_rates = load_fx_rates("data/processed/fx_rates.csv")

valuation_date, latest_prices = get_latest_prices(prices)

df = merge_positions_with_prices(positions, latest_prices)
df = calculate_local_market_values(df)
df = add_fx_rates(df, fx_rates, valuation_date)
df = calculate_usd_market_values(df)
df = portfolio_weights(df)

portfolio_value = df["market_value_usd"].sum()
stress_results, stress_summary = run_stress_tests(df)

usd_prices = convert_prices_to_usd(prices, fx_rates)
usd_prices = pivot_usd_prices(usd_prices)
returns = daily_return(usd_prices)

pnl = historical_pnl(returns, df)
loss_data = losses(pnl)

worst_scenarios = loss_data.nlargest(5, "loss")

var_95 = value_at_risk(loss_data, 0.95)
var_99 = value_at_risk(loss_data, 0.99)
es_95 = expected_shortfall(loss_data, 0.95)
es_99 = expected_shortfall(loss_data, 0.99)

risk_summary = pd.DataFrame(
    {
        "metric": ["95% VaR", "95% ES", "99% VaR", "99% ES"],
        "value_usd": [var_95, es_95, var_99, es_99],
        "percent_of_portfolio": [
            var_95 / portfolio_value,
            es_95 / portfolio_value,
            var_99 / portfolio_value,
            es_99 / portfolio_value,
        ],
    }
)

print(f"Valuation date: {valuation_date.date()}")
print(f"Portfolio value: USD {portfolio_value:,.2f}")
print(df[["asset_name", "market_value_usd", "portfolio_weight"]])
print(f"95% VaR: USD {var_95:,.2f}")
print(f"95% ES:  USD {es_95:,.2f}")
print(f"99% VaR: USD {var_99:,.2f}")
print(f"99% ES:  USD {es_99:,.2f}")
print("Worst five scenarios:")
print(worst_scenarios)

df.to_csv("outputs/risk_results/portfolio_valuation.csv", index=False)
worst_scenarios.to_csv("outputs/risk_results/worst_scenarios.csv", index=True, index_label="date")
risk_summary.to_csv("outputs/risk_results/risk_summary.csv", index=False)
stress_results.to_csv("outputs/risk_results/stress_test_details.csv", index=False)

stress_summary.to_csv("outputs/risk_results/stress_test_summary.csv", index=False)

chart_data = df.sort_values("portfolio_weight")

plt.figure(figsize=(10, 6))
plt.barh(
    chart_data["asset_name"],
    chart_data["portfolio_weight"] * 100,
)
plt.xlabel("Portfolio Weight (%)")
plt.title("Portfolio Allocation by Asset")
plt.tight_layout()
plt.savefig(
    "outputs/charts/portfolio_allocation.png",
    dpi=150,
)
plt.close()

plt.figure(figsize=(10, 6))
plt.hist(
    loss_data["loss"],
    bins=30,
    edgecolor="black",
)
plt.axvline(var_95, color="orange", linestyle="--", label=f"95% VaR: USD {var_95:,.2f}")
plt.axvline(var_99, color="red", linestyle="--", label=f"99% VaR: USD {var_99:,.2f}")
plt.xlabel("One-Day Loss (USD)")
plt.ylabel("Number of Scenarios")
plt.title("Historical Simulation Loss Distribution")
plt.legend()
plt.tight_layout()
plt.savefig(
    "outputs/charts/loss_distribution.png",
    dpi=150,
)
plt.close()

worst_date = worst_scenarios.index[0]
asset_columns = returns.columns
worst_day_pnl = worst_scenarios.loc[worst_date, asset_columns].sort_values()

asset_names = df.set_index("asset_id")["asset_name"]
worst_day_pnl.index = worst_day_pnl.index.map(asset_names)

plt.figure(figsize=(10, 6))
plt.barh(
    worst_day_pnl.index,
    worst_day_pnl.values,
    color="firebrick",
)
plt.axvline(0, color="black", linewidth=1)
plt.xlabel("P&L Contribution (USD)")
plt.title(f"Worst Scenario Contributions ({worst_date.date()})")
plt.tight_layout()
plt.savefig("outputs/charts/worst_scenario_contributions.png", dpi=150)
plt.close()

stress_chart = stress_summary.sort_values("loss_percent")

plt.figure(figsize=(10, 6))

bars = plt.barh(stress_chart["scenario"], stress_chart["loss_percent"] * 100, color="darkred")

plt.bar_label(bars, fmt="%.1f%%")
plt.xlabel("Portfolio Loss (%)")
plt.title("Portfolio Loss Under Stress Scenarios")
plt.tight_layout()
plt.savefig("outputs/charts/stress_test_losses.png", dpi=150)
plt.close()
