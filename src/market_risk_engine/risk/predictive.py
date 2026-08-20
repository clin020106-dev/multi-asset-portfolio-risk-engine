"""Predictive tail-risk calculations for the market-risk case study."""

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

BASE_FEATURES = [
    "return_1d",
    "return_5d",
    "return_20d",
    "volatility_5d",
    "volatility_20d",
    "equity_return_5d",
    "bond_return_5d",
    "gold_return_5d",
]

RATE_FEATURES = [
    "fed_funds_rate",
    "fed_rate_change_20d",
    "treasury_2y_change_5d",
    "treasury_10y_change_5d",
    "yield_curve",
    "yield_curve_change_20d",
]


def full_usd_price_history(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.pivot(index="date", columns="asset_id", values="price_usd")
    df = df.dropna()
    df = df.sort_index()

    return df


def portfolio_daily_returns(
    prices: pd.DataFrame,
    positions: pd.DataFrame,
) -> pd.DataFrame:
    df = prices.pct_change()
    df = df.dropna()

    weights = positions.set_index("asset_id")["portfolio_weight"]
    df["portfolio_return"] = df.mul(weights, axis=1).sum(axis=1)

    return df


def create_high_loss_target(returns: pd.DataFrame) -> pd.DataFrame:
    df = returns.copy()
    df["loss_threshold"] = df["portfolio_return"].rolling(window=252).quantile(0.10)
    df["next_day_return"] = df["portfolio_return"].shift(-1)
    df["high_loss"] = (df["next_day_return"] < df["loss_threshold"]).astype(int)
    df = df.dropna()

    return df


def create_predictive_features(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    df["return_1d"] = df["portfolio_return"]
    df["return_5d"] = df["portfolio_return"].rolling(window=5).mean()
    df["return_20d"] = df["portfolio_return"].rolling(window=20).mean()
    df["volatility_5d"] = df["portfolio_return"].rolling(window=5).std()
    df["volatility_20d"] = df["portfolio_return"].rolling(window=20).std()
    df["equity_return_5d"] = df["US_EQUITY"].rolling(window=5).mean()
    df["bond_return_5d"] = df["US_GOV_BOND"].rolling(window=5).mean()
    df["gold_return_5d"] = df["GOLD"].rolling(window=5).mean()
    df = df.dropna()

    return df


def add_interest_rate_features(data: pd.DataFrame, interest_rates: pd.DataFrame) -> pd.DataFrame:
    df = data.reset_index()
    rates = interest_rates.copy()
    rate_columns = ["fed_funds_rate", "treasury_2y_yield", "treasury_10y_yield"]
    rates[rate_columns] = rates[rate_columns].shift(1)

    df = df.merge(rates, on="date", how="left")
    df["fed_rate_change_20d"] = df["fed_funds_rate"].diff(20)
    df["treasury_2y_change_5d"] = df["treasury_2y_yield"].diff(5)
    df["treasury_10y_change_5d"] = df["treasury_10y_yield"].diff(5)
    df["yield_curve"] = df["treasury_10y_yield"] - df["treasury_2y_yield"]
    df["yield_curve_change_20d"] = df["yield_curve"].diff(20)
    df = df.dropna()
    df = df.set_index("date")

    return df


def train_logistic_model(
    train: pd.DataFrame, feature_columns: list[str]
) -> tuple[LogisticRegression, StandardScaler]:
    scaler = StandardScaler()
    x_train = scaler.fit_transform(train[feature_columns])
    model = LogisticRegression(class_weight="balanced", max_iter=1_000, random_state=42)
    model.fit(x_train, train["high_loss"])

    return model, scaler


def train_xgboost_model(train: pd.DataFrame, feature_columns: list[str]) -> XGBClassifier:
    target = train["high_loss"]
    negative_count = int((target == 0).sum())
    positive_count = int((target == 1).sum())
    class_ratio = negative_count / positive_count

    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        scale_pos_weight=class_ratio,
        random_state=42,
        eval_metric="logloss",
    )
    model.fit(train[feature_columns], target)

    return model


def classification_metrics(
    actual: pd.Series, probability: pd.Series, threshold: float = 0.50
) -> dict[str, float | int]:
    prediction = (probability >= threshold).astype(int)
    true_negative, false_positive, false_negative, true_positive = confusion_matrix(
        actual, prediction, labels=[0, 1]
    ).ravel()

    return {
        "observations": len(actual),
        "high_loss_days": int(actual.sum()),
        "event_rate": float(actual.mean()),
        "roc_auc": float(roc_auc_score(actual, probability)),
        "average_precision": float(average_precision_score(actual, probability)),
        "precision": float(precision_score(actual, prediction, zero_division=0)),
        "recall": float(recall_score(actual, prediction, zero_division=0)),
        "f1_score": float(f1_score(actual, prediction, zero_division=0)),
        "true_negative": int(true_negative),
        "false_positive": int(false_positive),
        "false_negative": int(false_negative),
        "true_positive": int(true_positive),
    }


def walk_forward_evaluation(
    data: pd.DataFrame,
    test_years: range,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    configurations = [
        ("Volatility score", "volatility", ["volatility_20d"]),
        ("Logistic (market)", "logistic", BASE_FEATURES),
        ("Logistic (+ rates)", "logistic", BASE_FEATURES + RATE_FEATURES),
        ("XGBoost (market)", "xgboost", BASE_FEATURES),
        ("XGBoost (+ rates)", "xgboost", BASE_FEATURES + RATE_FEATURES),
    ]
    metric_rows: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []

    for year in test_years:
        train = data.loc[data.index < f"{year}-01-01"].copy()
        test = data.loc[(data.index >= f"{year}-01-01") & (data.index < f"{year + 1}-01-01")].copy()

        for model_name, model_type, feature_columns in configurations:
            threshold = 0.50
            if model_type == "volatility":
                probability_values = test["volatility_20d"].to_numpy()
                threshold = float(train["volatility_20d"].quantile(0.90))
            elif model_type == "logistic":
                model, scaler = train_logistic_model(train, feature_columns)
                probability_values = model.predict_proba(scaler.transform(test[feature_columns]))[
                    :, 1
                ]
            else:
                model = train_xgboost_model(train, feature_columns)
                probability_values = model.predict_proba(test[feature_columns])[:, 1]

            probability = pd.Series(probability_values, index=test.index)
            metrics = classification_metrics(test["high_loss"], probability, threshold=threshold)
            metric_rows.append({"year": year, "model": model_name, **metrics})

            prediction_rows.append(
                pd.DataFrame(
                    {
                        "date": test.index,
                        "year": year,
                        "model": model_name,
                        "actual": test["high_loss"].to_numpy(),
                        "risk_score": probability_values,
                        "predicted_class": (probability_values >= threshold).astype(int),
                        "threshold": threshold,
                    }
                )
            )

    return pd.DataFrame(metric_rows), pd.concat(prediction_rows, ignore_index=True)
