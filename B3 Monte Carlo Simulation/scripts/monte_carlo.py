"""Monte Carlo NAV projection for selected mutual-fund schemes.

The model estimates five-year NAV paths using a geometric Brownian motion
process calibrated from historical daily log returns. Historical NAVs are
converted to business-day observations so repeated weekend/holiday values do
not artificially reduce volatility.

Outputs:
    data/processed/monte_carlo_projection.csv
    data/processed/monte_carlo_summary.csv
    PNGs/monte_carlo_projection.png
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
NAV_PATH = ROOT_DIR / "data" / "processed" / "02_nav_history_cleaned.csv"
PERFORMANCE_PATH = ROOT_DIR / "data" / "processed" / "07_scheme_performance_cleaned.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "processed"
PNG_DIR = ROOT_DIR / "PNGs"
TRADING_DAYS = 252
DEFAULT_YEARS = 5
DEFAULT_SIMULATIONS = 10_000
DEFAULT_TOP_N = 5
RANDOM_SEED = 42

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load cleaned NAV and scheme-performance datasets."""
    for path in (NAV_PATH, PERFORMANCE_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Required input file not found: {path}")
    nav = pd.read_csv(NAV_PATH, parse_dates=["date"])
    performance = pd.read_csv(PERFORMANCE_PATH)
    required_nav = {"date", "amfi_code", "nav"}
    required_perf = {"amfi_code", "scheme_name", "return_5yr_pct"}
    if missing := required_nav - set(nav.columns):
        raise ValueError(f"NAV dataset missing columns: {sorted(missing)}")
    if missing := required_perf - set(performance.columns):
        raise ValueError(f"Performance dataset missing columns: {sorted(missing)}")
    return nav, performance


def select_funds(performance: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Select top schemes by reported five-year return that have NAV history."""
    selected = (
        performance.sort_values("return_5yr_pct", ascending=False)
        .drop_duplicates("amfi_code")
        .head(top_n)
        .copy()
    )
    return selected[["amfi_code", "scheme_name", "return_5yr_pct"]]


def historical_parameters(nav: pd.DataFrame, code: int) -> tuple[float, float, float]:
    """Return latest NAV, annualised drift and annualised volatility."""
    series = nav.loc[nav["amfi_code"] == code, ["date", "nav"]].copy()
    series = series.sort_values("date").drop_duplicates("date").set_index("date")
    # The ETL contains forward-filled calendar dates. Keep business days for
    # return estimation so weekends/holidays are not treated as observations.
    series = series.resample("B").last().ffill().dropna()
    log_returns = np.log(series["nav"] / series["nav"].shift(1)).dropna()
    if len(log_returns) < 60:
        raise ValueError(f"Insufficient NAV history for AMFI code {code}.")
    mu_daily = float(log_returns.mean())
    sigma_daily = float(log_returns.std(ddof=1))
    mu_annual = mu_daily * TRADING_DAYS
    sigma_annual = sigma_daily * np.sqrt(TRADING_DAYS)
    latest_nav = float(series["nav"].iloc[-1])
    return latest_nav, mu_annual, sigma_annual


def simulate(
    latest_nav: float,
    mu: float,
    sigma: float,
    years: int,
    simulations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Simulate NAV paths using geometric Brownian motion."""
    steps = years * TRADING_DAYS
    dt = 1.0 / TRADING_DAYS
    shocks = rng.standard_normal((steps, simulations))
    increments = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shocks
    paths = np.empty((steps + 1, simulations), dtype=np.float64)
    paths[0] = latest_nav
    paths[1:] = latest_nav * np.exp(np.cumsum(increments, axis=0))
    return paths


def summarise_paths(paths: np.ndarray, latest_nav: float) -> pd.DataFrame:
    """Create median and uncertainty-band projections by trading day."""
    q05, q25, q50, q75, q95 = np.quantile(paths, [0.05, 0.25, 0.50, 0.75, 0.95], axis=1)
    return pd.DataFrame(
        {
            "trading_day": np.arange(len(q50)),
            "nav_p05": q05,
            "nav_p25": q25,
            "nav_median": q50,
            "nav_p75": q75,
            "nav_p95": q95,
            "starting_nav": latest_nav,
        }
    )


def plot_projection(results: dict[str, pd.DataFrame], output_path: Path) -> None:
    """Save a clean projection chart for the selected schemes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 7))
    for scheme_name, frame in results.items():
        x = frame["trading_day"] / TRADING_DAYS
        line = ax.plot(x, frame["nav_median"], linewidth=2, label=scheme_name)[0]
        ax.fill_between(x, frame["nav_p05"], frame["nav_p95"], alpha=0.08, color=line.get_color())
    ax.set_title("5-Year Monte Carlo NAV Projection", fontsize=20, fontweight="bold", loc="left")
    ax.set_xlabel("Years")
    ax.set_ylabel("Projected NAV")
    ax.grid(alpha=0.18)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def run(top_n: int = DEFAULT_TOP_N, years: int = DEFAULT_YEARS, simulations: int = DEFAULT_SIMULATIONS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the Monte Carlo analysis and save projection/summary outputs."""
    nav, performance = load_inputs()
    selected = select_funds(performance, top_n)
    rng = np.random.default_rng(RANDOM_SEED)
    all_projection: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []
    plot_results: dict[str, pd.DataFrame] = {}

    for row in selected.itertuples(index=False):
        latest_nav, mu, sigma = historical_parameters(nav, int(row.amfi_code))
        paths = simulate(latest_nav, mu, sigma, years, simulations, rng)
        projection = summarise_paths(paths, latest_nav)
        projection.insert(0, "scheme_name", row.scheme_name)
        projection.insert(1, "amfi_code", int(row.amfi_code))
        all_projection.append(projection)
        terminal = paths[-1]
        summary_rows.append(
            {
                "amfi_code": int(row.amfi_code),
                "scheme_name": row.scheme_name,
                "historical_5yr_return_pct": float(row.return_5yr_pct),
                "starting_nav": latest_nav,
                "annualised_historical_drift_pct": mu * 100,
                "annualised_volatility_pct": sigma * 100,
                "projected_nav_median_5yr": float(np.median(terminal)),
                "projected_nav_p05_5yr": float(np.quantile(terminal, 0.05)),
                "projected_nav_p95_5yr": float(np.quantile(terminal, 0.95)),
                "probability_positive_growth_pct": float((terminal > latest_nav).mean() * 100),
            }
        )
        plot_results[row.scheme_name] = projection

    projection_df = pd.concat(all_projection, ignore_index=True)
    summary_df = pd.DataFrame(summary_rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    projection_df.to_csv(OUTPUT_DIR / "monte_carlo_projection.csv", index=False)
    summary_df.to_csv(OUTPUT_DIR / "monte_carlo_summary.csv", index=False)
    plot_projection(plot_results, PNG_DIR / "monte_carlo_projection.png")
    logger.info("Monte Carlo analysis completed for %d schemes.", len(selected))
    return projection_df, summary_df


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--years", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--simulations", type=int, default=DEFAULT_SIMULATIONS)
    return parser.parse_args()


def main() -> None:
    """Run the Monte Carlo projection."""
    args = parse_args()
    run(top_n=args.top_n, years=args.years, simulations=args.simulations)


if __name__ == "__main__":
    main()
