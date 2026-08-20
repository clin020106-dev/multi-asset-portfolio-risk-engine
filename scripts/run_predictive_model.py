"""Run the predictive tail-risk extension and write portfolio-ready outputs."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from market_risk_engine.data.loaders import (
    load_fx_rates,
    load_interest_rates,
    load_positions,
    load_prices,
)
from market_risk_engine.portfolio.valuation import (
    add_fx_rates,
    calculate_local_market_values,
    calculate_usd_market_values,
    get_latest_prices,
    merge_positions_with_prices,
    portfolio_weights,
)
from market_risk_engine.risk.historical import convert_prices_to_usd
from market_risk_engine.risk.predictive import (
    BASE_FEATURES,
    RATE_FEATURES,
    add_interest_rate_features,
    create_high_loss_target,
    create_predictive_features,
    full_usd_price_history,
    portfolio_daily_returns,
    train_logistic_model,
    train_xgboost_model,
    walk_forward_evaluation,
)

MODEL_RESULTS_DIR = Path("outputs/model_results")
CHARTS_DIR = Path("outputs/charts")
MODEL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

positions = load_positions("data/processed/positions.csv")
prices = load_prices("data/processed/prices.csv")
fx_rates = load_fx_rates("data/processed/fx_rates.csv")
interest_rates = load_interest_rates("data/processed/rates.csv")

valuation_date, latest_prices = get_latest_prices(prices)
portfolio = merge_positions_with_prices(positions, latest_prices)
portfolio = calculate_local_market_values(portfolio)
portfolio = add_fx_rates(portfolio, fx_rates, valuation_date)
portfolio = calculate_usd_market_values(portfolio)
portfolio = portfolio_weights(portfolio)

usd_prices = convert_prices_to_usd(prices, fx_rates)
usd_prices = full_usd_price_history(usd_prices)
returns = portfolio_daily_returns(usd_prices, portfolio)

model_data = create_high_loss_target(returns)
model_data = create_predictive_features(model_data)
model_data = add_interest_rate_features(model_data, interest_rates)

walk_forward_metrics, walk_forward_predictions = walk_forward_evaluation(
    model_data, test_years=range(2020, 2026)
)

model_summary = walk_forward_metrics.groupby("model", as_index=False).agg(
    folds=("year", "count"),
    mean_roc_auc=("roc_auc", "mean"),
    std_roc_auc=("roc_auc", "std"),
    mean_average_precision=("average_precision", "mean"),
    std_average_precision=("average_precision", "std"),
    mean_precision=("precision", "mean"),
    mean_recall=("recall", "mean"),
    mean_f1_score=("f1_score", "mean"),
    mean_event_rate=("event_rate", "mean"),
    total_true_positive=("true_positive", "sum"),
    total_false_positive=("false_positive", "sum"),
    total_false_negative=("false_negative", "sum"),
)
model_summary["average_precision_lift"] = (
    model_summary["mean_average_precision"] / model_summary["mean_event_rate"]
)

primary_model_name = "Logistic (market)"
primary_features = BASE_FEATURES
primary_model, primary_scaler = train_logistic_model(model_data, primary_features)

xgb_model_name = "XGBoost (market)"
xgb_model = train_xgboost_model(model_data, BASE_FEATURES)
xgb_rate_model_name = "XGBoost (+ rates)"
xgb_rate_features = BASE_FEATURES + RATE_FEATURES
xgb_rate_model = train_xgboost_model(model_data, xgb_rate_features)

latest_features = create_predictive_features(returns)
latest_features = add_interest_rate_features(latest_features, interest_rates)
prediction_date = latest_features.index.max()

primary_latest_x = primary_scaler.transform(
    latest_features.loc[[prediction_date], primary_features]
)
primary_risk_score = float(primary_model.predict_proba(primary_latest_x)[0, 1])

prediction_rows = [
    {
        "prediction_date": prediction_date,
        "model": primary_model_name,
        "risk_score": primary_risk_score,
        "predicted_class": int(primary_risk_score >= 0.50),
        "threshold": 0.50,
    }
]
for model_name, model, feature_columns in [
    (xgb_model_name, xgb_model, BASE_FEATURES),
    (xgb_rate_model_name, xgb_rate_model, xgb_rate_features),
]:
    latest_x = latest_features.loc[[prediction_date], feature_columns]
    risk_score = float(model.predict_proba(latest_x)[0, 1])
    prediction_rows.append(
        {
            "prediction_date": prediction_date,
            "model": model_name,
            "risk_score": risk_score,
            "predicted_class": int(risk_score >= 0.50),
            "threshold": 0.50,
        }
    )

latest_prediction = pd.DataFrame(prediction_rows)
feature_importance = pd.DataFrame(
    {"feature": BASE_FEATURES, "importance": xgb_model.feature_importances_}
).sort_values("importance", ascending=False)
logistic_coefficients = pd.DataFrame(
    {"feature": primary_features, "coefficient": primary_model.coef_[0]}
).sort_values("coefficient")

walk_forward_metrics.to_csv(MODEL_RESULTS_DIR / "walk_forward_metrics.csv", index=False)
walk_forward_predictions.to_csv(MODEL_RESULTS_DIR / "walk_forward_predictions.csv", index=False)
model_summary.to_csv(MODEL_RESULTS_DIR / "model_summary.csv", index=False)
feature_importance.to_csv(MODEL_RESULTS_DIR / "feature_importance.csv", index=False)
logistic_coefficients.to_csv(MODEL_RESULTS_DIR / "logistic_coefficients.csv", index=False)
latest_prediction.to_csv(MODEL_RESULTS_DIR / "latest_prediction.csv", index=False)

plt.style.use("seaborn-v0_8-whitegrid")
model_order = [
    "Volatility score",
    "Logistic (market)",
    "Logistic (+ rates)",
    "XGBoost (market)",
    "XGBoost (+ rates)",
]
model_colors = {
    "Volatility score": "#777777",
    "Logistic (market)": "#4C78A8",
    "Logistic (+ rates)": "#9ECAE9",
    "XGBoost (market)": "#F58518",
    "XGBoost (+ rates)": "#FFBF79",
}

plt.figure(figsize=(10, 6))
for model_name in model_order:
    chart_data = walk_forward_metrics.loc[walk_forward_metrics["model"] == model_name]
    plt.plot(
        chart_data["year"],
        chart_data["average_precision"],
        marker="o",
        linewidth=2,
        label=model_name,
        color=model_colors[model_name],
    )

event_rate_by_year = walk_forward_metrics.drop_duplicates("year")
plt.plot(
    event_rate_by_year["year"],
    event_rate_by_year["event_rate"],
    color="#555555",
    linestyle="--",
    linewidth=1.5,
    label="Event-rate baseline",
)
plt.xlabel("Test Year")
plt.ylabel("Average Precision")
plt.title("Walk-Forward Tail-Risk Performance by Year")
plt.legend(ncol=2)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "walk_forward_average_precision.png", dpi=180)
plt.close()

summary_chart = model_summary.set_index("model").loc[model_order]
x_positions = np.arange(len(model_order))
short_labels = [
    "Volatility\nscore",
    "Logistic\nmarket",
    "Logistic\n+ rates",
    "XGBoost\nmarket",
    "XGBoost\n+ rates",
]

figure, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].bar(
    x_positions, summary_chart["mean_roc_auc"], color=[model_colors[name] for name in model_order]
)
axes[0].axhline(0.50, color="#555555", linestyle="--", linewidth=1.5)
axes[0].set_xticks(x_positions, short_labels)
axes[0].set_ylim(0, 1)
axes[0].set_ylabel("Mean ROC-AUC")
axes[0].set_title("Ranking Performance")
axes[0].bar_label(axes[0].containers[0], fmt="%.3f", padding=3)

axes[1].bar(
    x_positions,
    summary_chart["mean_average_precision"],
    color=[model_colors[name] for name in model_order],
)
axes[1].axhline(
    summary_chart["mean_event_rate"].mean(), color="#555555", linestyle="--", linewidth=1.5
)
axes[1].set_xticks(x_positions, short_labels)
axes[1].set_ylim(0, 0.20)
axes[1].set_ylabel("Mean Average Precision")
axes[1].set_title("Rare-Event Performance")
axes[1].bar_label(axes[1].containers[0], fmt="%.3f", padding=3)

figure.suptitle("Six-Year Walk-Forward Model Comparison")
figure.tight_layout()
figure.savefig(CHARTS_DIR / "walk_forward_model_comparison.png", dpi=180)
plt.close(figure)

primary_predictions = walk_forward_predictions.loc[
    walk_forward_predictions["model"] == primary_model_name
]
precision_values, recall_values, _ = precision_recall_curve(
    primary_predictions["actual"], primary_predictions["risk_score"]
)
pooled_event_rate = primary_predictions["actual"].mean()

plt.figure(figsize=(8, 6))
plt.plot(
    recall_values,
    precision_values,
    color=model_colors[primary_model_name],
    linewidth=2,
    label=primary_model_name,
)
plt.axhline(
    pooled_event_rate,
    color="#555555",
    linestyle="--",
    linewidth=1.5,
    label=f"Event-rate baseline ({pooled_event_rate:.1%})",
)
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Pooled Walk-Forward Precision-Recall Curve")
plt.legend()
plt.tight_layout()
plt.savefig(CHARTS_DIR / "walk_forward_precision_recall.png", dpi=180)
plt.close()

importance_chart = feature_importance.sort_values("importance")
plt.figure(figsize=(9, 5))
plt.barh(
    importance_chart["feature"],
    importance_chart["importance"],
    color=model_colors[primary_model_name],
)
plt.xlabel("Relative Importance")
plt.title("XGBoost Market-Feature Importance")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "xgboost_feature_importance.png", dpi=180)
plt.close()

coefficient_colors = [
    "#4C78A8" if value < 0 else "#E45756" for value in logistic_coefficients["coefficient"]
]
plt.figure(figsize=(9, 5))
plt.barh(
    logistic_coefficients["feature"], logistic_coefficients["coefficient"], color=coefficient_colors
)
plt.axvline(0, color="#555555", linewidth=1)
plt.xlabel("Standardized Coefficient")
plt.title("Primary Logistic Model Coefficients")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "logistic_model_coefficients.png", dpi=180)
plt.close()

print("Walk-forward model summary:")
print(
    model_summary[
        [
            "model",
            "mean_roc_auc",
            "mean_average_precision",
            "mean_precision",
            "mean_recall",
            "mean_f1_score",
            "average_precision_lift",
        ]
    ]
    .round(3)
    .to_string(index=False)
)
print("Latest risk scores:")
print(latest_prediction.to_string(index=False))
print(f"Saved model outputs to {MODEL_RESULTS_DIR}")
print(f"Saved predictive charts to {CHARTS_DIR}")
