# Bonus B3 — Monte Carlo NAV Simulation

## Objective
Project NAV growth over five years with uncertainty bands using historical NAV behaviour from the capstone dataset.

## Method
- Historical NAV is converted to business-day observations.
- Daily log returns are calculated from the cleaned NAV history.
- Annual drift is estimated as mean daily log return × 252.
- Annual volatility is estimated as daily log-return standard deviation × √252.
- Geometric Brownian Motion is used for the simulation.
- 10,000 paths are generated for each of the five selected schemes.
- The 5th and 95th percentiles form the uncertainty band.

## Selected schemes
The default selection is the top five schemes by reported five-year return in `07_scheme_performance_cleaned.csv` that have NAV history.

## Run
From the project root:

```bash
python scripts/monte_carlo.py
```

Optional:

```bash
python scripts/monte_carlo.py --top-n 5 --years 5 --simulations 10000
```

## Outputs
- `data/processed/monte_carlo_projection.csv`
- `data/processed/monte_carlo_summary.csv`
- `PNGs/monte_carlo_projection.png`
- `notebooks/06_Monte_Carlo_Simulation.ipynb`

## Interpretation note
Monte Carlo outputs are scenario projections rather than guaranteed forecasts. The results depend strongly on the historical drift and volatility assumptions and should not be interpreted as investment advice.
