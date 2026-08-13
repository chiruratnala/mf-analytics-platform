"""Build a Markowitz Efficient Frontier for five selected mutual funds.

The five funds are selected as the top five schemes by reported 5-year return
from the project's cleaned performance dataset, restricted to schemes with
available NAV history. Daily portfolio statistics use business-day observations.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NAV_PATH = PROJECT_ROOT / "data" / "processed" / "02_nav_history_cleaned.csv"
PERF_PATH = PROJECT_ROOT / "data" / "processed" / "07_scheme_performance_cleaned.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
PNG_DIR = PROJECT_ROOT / "PNGs"

TRADING_DAYS = 252
DEFAULT_TOP_N = 5
RANDOM_PORTFOLIOS = 50_000

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load cleaned NAV and scheme-performance datasets."""
    for path in (NAV_PATH, PERF_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")
    nav = pd.read_csv(NAV_PATH, parse_dates=["date"])
    perf = pd.read_csv(PERF_PATH)
    required_nav = {"date", "amfi_code", "nav"}
    required_perf = {"amfi_code", "scheme_name", "return_5yr_pct"}
    if missing := required_nav - set(nav.columns):
        raise ValueError(f"NAV dataset missing columns: {sorted(missing)}")
    if missing := required_perf - set(perf.columns):
        raise ValueError(f"Performance dataset missing columns: {sorted(missing)}")
    return nav, perf


def select_funds(nav: pd.DataFrame, perf: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Select the top schemes by reported 5-year return with NAV coverage."""
    available = set(nav["amfi_code"].dropna().astype(int))
    eligible = (
        perf.assign(amfi_code=pd.to_numeric(perf["amfi_code"], errors="coerce"))
        .dropna(subset=["amfi_code", "return_5yr_pct", "category"])
        .assign(amfi_code=lambda x: x["amfi_code"].astype(int))
        .query("amfi_code in @available")
        .sort_values("return_5yr_pct", ascending=False)
        .copy()
    )
    # Prefer one high-performing scheme from each major equity category to
    # avoid selecting duplicate plan variants or a single-category portfolio.
    preferred_categories = ["Small Cap", "Mid Cap", "Flexi Cap", "Large & Mid Cap", "Large Cap"]
    chosen = []
    for category in preferred_categories:
        match = eligible[eligible["category"].eq(category)]
        if not match.empty:
            chosen.append(match.iloc[0])
        if len(chosen) == top_n:
            break
    if len(chosen) < top_n:
        used_codes = {int(row["amfi_code"]) for row in chosen}
        for _, row in eligible.iterrows():
            if int(row["amfi_code"]) not in used_codes:
                chosen.append(row)
                used_codes.add(int(row["amfi_code"]))
            if len(chosen) == top_n:
                break
    selected = pd.DataFrame(chosen)
    if len(selected) < top_n:
        raise ValueError(f"Only {len(selected)} funds have both performance and NAV data.")
    return selected[["amfi_code", "scheme_name", "category", "return_5yr_pct"]].reset_index(drop=True)


def build_returns(nav: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    """Create aligned business-day return series for the selected schemes."""
    codes = selected["amfi_code"].tolist()
    pivot = (
        nav[nav["amfi_code"].isin(codes)]
        .pivot_table(index="date", columns="amfi_code", values="nav", aggfunc="last")
        .sort_index()
    )
    business_days = pd.date_range(pivot.index.min(), pivot.index.max(), freq="B")
    prices = pivot.reindex(business_days).ffill()
    prices = prices.dropna(how="all").ffill()
    returns = prices.pct_change().dropna(how="all")
    returns = returns.dropna(axis=1, how="all")
    if returns.shape[1] < len(codes):
        raise ValueError("Insufficient overlapping NAV history for all selected funds.")
    return returns.dropna()


def portfolio_stats(weights: np.ndarray, mean_returns: np.ndarray, covariance: np.ndarray) -> tuple[float, float, float]:
    """Return annualised portfolio return, volatility and Sharpe ratio."""
    ret = float(weights @ mean_returns)
    vol = float(np.sqrt(weights @ covariance @ weights))
    sharpe = ret / vol if vol > 0 else 0.0
    return ret, vol, sharpe


def optimize_portfolio(mean_returns: np.ndarray, covariance: np.ndarray, target_return: float | None = None, objective: str = "sharpe") -> np.ndarray:
    """Optimise weights under long-only, fully-invested constraints."""
    n = len(mean_returns)
    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    if target_return is not None:
        constraints.append({"type": "eq", "fun": lambda w: w @ mean_returns - target_return})

    equal = np.full(n, 1.0 / n)

    if objective == "min_vol":
        fun = lambda w: np.sqrt(w @ covariance @ w)
    elif objective == "sharpe":
        fun = lambda w: -(w @ mean_returns) / max(np.sqrt(w @ covariance @ w), 1e-12)
    else:
        raise ValueError("objective must be 'min_vol' or 'sharpe'")

    result = minimize(fun, equal, method="SLSQP", bounds=bounds, constraints=constraints,
                      options={"maxiter": 2000, "ftol": 1e-10})
    if not result.success:
        raise RuntimeError(f"Portfolio optimisation failed: {result.message}")
    return result.x


def main(top_n: int = DEFAULT_TOP_N, random_portfolios: int = RANDOM_PORTFOLIOS) -> None:
    """Generate portfolio samples, efficient frontier and summary outputs."""
    nav, perf = load_inputs()
    selected = select_funds(nav, perf, top_n)
    returns = build_returns(nav, selected)

    selected = selected[selected["amfi_code"].isin(returns.columns)].copy()
    returns = returns[selected["amfi_code"].tolist()]
    names = selected["scheme_name"].tolist()

    mean_returns = returns.mean().to_numpy() * TRADING_DAYS
    covariance = returns.cov().to_numpy() * TRADING_DAYS

    rng = np.random.default_rng(42)
    weights = rng.dirichlet(np.ones(top_n), size=random_portfolios)
    portfolio_returns = weights @ mean_returns
    portfolio_vols = np.sqrt(np.einsum("ij,jk,ik->i", weights, covariance, weights))
    portfolio_sharpes = portfolio_returns / np.maximum(portfolio_vols, 1e-12)

    min_idx = np.argmin(portfolio_vols)
    max_sharpe_idx = np.argmax(portfolio_sharpes)

    min_vol_weights = optimize_portfolio(mean_returns, covariance, objective="min_vol")
    max_sharpe_weights = optimize_portfolio(mean_returns, covariance, objective="sharpe")

    target_returns = np.linspace(mean_returns.min(), mean_returns.max(), 60)
    frontier = []
    for target in target_returns:
        try:
            w = optimize_portfolio(mean_returns, covariance, target_return=float(target), objective="min_vol")
            ret, vol, sharpe = portfolio_stats(w, mean_returns, covariance)
            frontier.append((ret, vol, sharpe, *w))
        except RuntimeError:
            continue

    columns = ["return_annual", "volatility_annual", "sharpe_ratio"] + [f"weight_{c}" for c in selected["amfi_code"]]
    frontier_df = pd.DataFrame(frontier, columns=columns)
    samples = pd.DataFrame({
        "return_annual": portfolio_returns,
        "volatility_annual": portfolio_vols,
        "sharpe_ratio": portfolio_sharpes,
    })
    for i, code in enumerate(selected["amfi_code"]):
        samples[f"weight_{code}"] = weights[:, i]

    summary_rows = []
    for label, w in [
        ("Minimum Volatility", min_vol_weights),
        ("Maximum Sharpe", max_sharpe_weights),
    ]:
        ret, vol, sharpe = portfolio_stats(w, mean_returns, covariance)
        row = {"portfolio": label, "return_annual": ret, "volatility_annual": vol, "sharpe_ratio": sharpe}
        for code, weight in zip(selected["amfi_code"], w):
            row[f"weight_{code}"] = weight
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)

    fund_stats = selected.copy()
    fund_stats["historical_daily_return_annual"] = mean_returns
    fund_stats["annual_volatility"] = np.sqrt(np.diag(covariance))
    fund_stats["sharpe_ratio_annual"] = mean_returns / np.maximum(fund_stats["annual_volatility"], 1e-12)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    selected.to_csv(OUTPUT_DIR / "markowitz_selected_funds.csv", index=False)
    fund_stats.to_csv(OUTPUT_DIR / "markowitz_fund_stats.csv", index=False)
    samples.to_csv(OUTPUT_DIR / "markowitz_random_portfolios.csv", index=False)
    frontier_df.to_csv(OUTPUT_DIR / "markowitz_efficient_frontier.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "markowitz_optimal_portfolios.csv", index=False)

    fig, ax = plt.subplots(figsize=(10.67, 8), facecolor="none")
    ax.set_facecolor("none")
    ax.scatter(portfolio_vols * 100, portfolio_returns * 100, s=5, alpha=0.12)
    if not frontier_df.empty:
        ax.plot(frontier_df["volatility_annual"] * 100, frontier_df["return_annual"] * 100, linewidth=2.5)
    ax.scatter(
        [np.sqrt(min_vol_weights @ covariance @ min_vol_weights) * 100],
        [min_vol_weights @ mean_returns * 100],
        s=90, marker="o", label="Minimum Volatility",
    )
    ax.scatter(
        [np.sqrt(max_sharpe_weights @ covariance @ max_sharpe_weights) * 100],
        [max_sharpe_weights @ mean_returns * 100],
        s=90, marker="*", label="Maximum Sharpe",
    )
    ax.set_title("Markowitz Efficient Frontier", fontsize=22, fontweight="bold", loc="left")
    ax.set_xlabel("Annualised Volatility (%)")
    ax.set_ylabel("Annualised Expected Return (%)")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PNG_DIR / "markowitz_efficient_frontier.png", dpi=300, transparent=True, bbox_inches="tight")
    plt.close(fig)

    logger.info("Selected funds: %s", " | ".join(names))
    logger.info("Minimum-volatility portfolio Sharpe: %.3f", summary.loc[0, "sharpe_ratio"])
    logger.info("Maximum-Sharpe portfolio Sharpe: %.3f", summary.loc[1, "sharpe_ratio"])
    logger.info("Markowitz outputs written to %s", OUTPUT_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--random-portfolios", type=int, default=RANDOM_PORTFOLIOS)
    args = parser.parse_args()
    main(args.top_n, args.random_portfolios)
