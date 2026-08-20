import pandas as pd

start_date = "2016-01-01"
end_date = "2026-01-01"

fed_funds_url = (f"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF&cosd={start_date}&coed={end_date}")

treasury_2y_url = (f"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&cosd={start_date}&coed={end_date}")

treasury_10y_url = (f"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd={start_date}&coed={end_date}")

fed_funds = pd.read_csv(fed_funds_url, na_values=".")

treasury_2y = pd.read_csv(treasury_2y_url, na_values=".")

treasury_10y = pd.read_csv(treasury_10y_url, na_values=".")

fed_funds.columns = ["date", "fed_funds_rate"]
treasury_2y.columns = ["date", "treasury_2y_yield"]
treasury_10y.columns = ["date", "treasury_10y_yield"]

rates = fed_funds.merge(treasury_2y, on="date", how="outer")

rates = rates.merge(treasury_10y, on="date", how="outer")

rates["date"] = pd.to_datetime(rates["date"])
rates = rates.sort_values("date")

rate_columns = ["fed_funds_rate", "treasury_2y_yield", "treasury_10y_yield"]

rates[rate_columns] = rates[rate_columns].ffill()
rates = rates.dropna()

rates.to_csv("data/processed/rates.csv",index=False)

print(rates.head())
print(rates.tail())
print(rates.shape)
print("Saved rate data to data/processed/rates.csv")
