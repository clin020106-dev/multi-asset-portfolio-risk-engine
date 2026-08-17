# Multi-Asset Portfolio Market Risk Engine

## v0.1 Scope

The goal of v0.1 is to estimate the one-day market risk of a multi-asset portfolio in USD using sample daily market data.

### Included in v0.1

- Base currency: USD
- Data frequency: Daily
- Risk horizon: 1 day
- Confidence levels: 95% and 99%
- Historical observation window: 250 trading days
- Method: Historical Simulation
- Risk measures: Value at Risk (VaR) and Expected Shortfall (ES)
- Data source: Project-provided sample data
- Intended use: local execution, learning, and portfolio risk analysis

### Out of scope for v0.1

- Real-time and intraday market data
- Automated connections to brokers, exchanges, or paid data providers
- VaR backtesting and model validation
- Stress testing and scenario analysis
- Parametric and Monte Carlo VaR methods
- Advanced derivatives pricing models
- Production deployment, user authentication, and graphical user interface

## v0.1 Completion Criteria

- [Methodology](docs/methodology.md) — Detailed inputs, assumptions, Historical Simulation process, VaR and ES calculations, outputs, and limitations.

> This project is for educational and demonstration purposes only and does not constitute investment advice.
