# B4 — Markowitz Efficient Frontier

This bonus challenge applies Modern Portfolio Theory (Markowitz mean-variance optimisation) to five selected mutual-fund schemes from the Bluestock capstone dataset.

## Selection
To make the portfolio more meaningful, the script selects one high-performing scheme with NAV history from each of these categories, where available:

- Small Cap
- Mid Cap
- Flexi Cap
- Large & Mid Cap
- Large Cap

Selection is based on the reported 5-year return in `07_scheme_performance_cleaned.csv`.

## Method
- Daily NAV observations are aligned to business days.
- Missing business-day NAV values are forward-filled.
- Daily returns are calculated from NAV.
- Expected returns and covariance are annualised using 252 trading days.
- Portfolios are long-only: each weight is between 0% and 100%.
- Portfolio weights sum to 100%.
- 50,000 random feasible portfolios are generated.
- The efficient frontier is obtained by minimising volatility for a sequence of target returns.
- Two optimised portfolios are reported:
  - Minimum Volatility
  - Maximum Sharpe Ratio

## Run

From the project root:

```bash
python scripts/markowitz_optimization.py
```

Optional:

```bash
python scripts/markowitz_optimization.py --top-n 5 --random-portfolios 50000
```

## Outputs

- `data/processed/markowitz_selected_funds.csv`
- `data/processed/markowitz_fund_stats.csv`
- `data/processed/markowitz_random_portfolios.csv`
- `data/processed/markowitz_efficient_frontier.csv`
- `data/processed/markowitz_optimal_portfolios.csv`
- `PNGs/markowitz_efficient_frontier.png`
- `notebooks/06_Markowitz_Efficient_Frontier.ipynb`

## Current selected schemes

The current run selected:

1. ABSL Small Cap Fund - Regular - Growth
2. DSP Midcap Fund - Regular - Growth
3. UTI Flexi Cap Fund - Regular - Growth
4. Mirae Asset Emerging Bluechip Fund - Regular - Growth
5. Nippon India Large Cap Fund - Direct - Growth

The optimisation is based on historical data and should be treated as an analytical scenario, not investment advice or a guarantee of future performance.
