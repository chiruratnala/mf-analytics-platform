"""
compute_metrics.py
------------------
Compute mutual-fund performance analytics for the Bluestock MF Capstone.

Outputs:
    data/processed/fund_scorecard.csv
    data/processed/alpha_beta.csv
    data/processed/daily_returns.csv
    data/processed/benchmark_comparison.png

Metrics:
    - Daily returns
    - 1Y / 3Y / 5Y CAGR
    - Sharpe ratio
    - Sortino ratio
    - Alpha and Beta vs Nifty 100
    - Maximum drawdown
    - Fund scorecard (0-100)
    - Tracking error vs benchmark

Run from the project root:
    python scripts/compute_metrics.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"

NAV_FILE = PROCESSED_DIR / "02_nav_history_cleaned.csv"
PERFORMANCE_FILE = PROCESSED_DIR / "07_scheme_performance_cleaned.csv"
BENCHMARK_FILE = PROCESSED_DIR / "10_benchmark_indices_cleaned.csv"

DAILY_RF = (1 + 0.065) ** (1 / 252) - 1
TRADING_DAYS = 252

OUTPUT_SCORECARD = PROCESSED_DIR / "fund_scorecard.csv"
OUTPUT_ALPHA_BETA = PROCESSED_DIR / "alpha_beta.csv"
OUTPUT_DAILY_RETURNS = PROCESSED_DIR / "daily_returns.csv"
OUTPUT_BENCHMARK_CHART = REPORT_DIR / "benchmark_comparison.png"


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def require_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    """Raise a clear error when required columns are missing."""
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"{name} is missing required columns: {missing}. "
            f"Available columns: {df.columns.tolist()}"
        )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from column names."""
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def calculate_cagr(nav_values: pd.Series, periods: int) -> float:
    """
    Calculate CAGR over a trading-period window.

    CAGR = (NAV_end / NAV_start) ** (252 / number_of_observations) - 1

    Returns NaN when insufficient observations or invalid NAV values exist.
    """
    values = nav_values.dropna()

    if len(values) < periods:
        return np.nan

    start = float(values.iloc[-periods])
    end = float(values.iloc[-1])

    if start <= 0 or end <= 0:
        return np.nan

    years = periods / TRADING_DAYS
    if years <= 0:
        return np.nan

    return (end / start) ** (1 / years) - 1


def calculate_max_drawdown(nav_values: pd.Series) -> tuple[float, pd.Timestamp | None]:
    """Return maximum drawdown and the date on which the worst drawdown occurs."""
    values = nav_values.dropna()

    if values.empty:
        return np.nan, None

    running_max = values.cummax()
    drawdown = values / running_max - 1

    worst_position = drawdown.idxmin()
    return float(drawdown.loc[worst_position]), worst_position


def calculate_sharpe(returns: pd.Series) -> float:
    """Annualised Sharpe ratio using a 6.5% annual risk-free proxy."""
    returns = returns.dropna()

    if len(returns) < 2:
        return np.nan

    excess = returns - DAILY_RF
    volatility = returns.std(ddof=1)

    if volatility == 0 or pd.isna(volatility):
        return np.nan

    return float(excess.mean() / volatility * np.sqrt(TRADING_DAYS))


def calculate_sortino(returns: pd.Series) -> float:
    """Annualised Sortino ratio using only negative daily returns as downside risk."""
    returns = returns.dropna()

    if len(returns) < 2:
        return np.nan

    excess = returns - DAILY_RF
    downside = returns[returns < 0]

    if downside.empty:
        return np.nan

    downside_std = downside.std(ddof=1)

    if downside_std == 0 or pd.isna(downside_std):
        return np.nan

    return float(excess.mean() / downside_std * np.sqrt(TRADING_DAYS))


def find_benchmark_columns(benchmark: pd.DataFrame) -> tuple[str, str, str | None]:
    """
    Detect benchmark date, name and value columns.

    Expected data normally contains something equivalent to:
        date, index_name, index_value

    The function also accepts common alternative names.
    """
    date_candidates = ["date", "Date"]
    name_candidates = [
        "index_name",
        "benchmark_name",
        "index",
        "name",
        "scheme_name",
    ]
    value_candidates = [
        "index_value",
        "benchmark_value",
        "close",
        "value",
        "nav",
    ]

    date_col = next((c for c in date_candidates if c in benchmark.columns), None)
    name_col = next((c for c in name_candidates if c in benchmark.columns), None)
    value_col = next((c for c in value_candidates if c in benchmark.columns), None)

    if date_col is None or name_col is None or value_col is None:
        raise ValueError(
            "Could not identify benchmark columns. Expected equivalents of "
            "'date', 'index_name', and 'index_value'. "
            f"Available columns: {benchmark.columns.tolist()}"
        )

    return date_col, name_col, value_col


def benchmark_returns(benchmark: pd.DataFrame) -> pd.DataFrame:
    """Prepare benchmark daily returns."""
    date_col, name_col, value_col = find_benchmark_columns(benchmark)

    b = benchmark[[date_col, name_col, value_col]].copy()
    b[date_col] = pd.to_datetime(b[date_col], errors="coerce")
    b[value_col] = pd.to_numeric(b[value_col], errors="coerce")

    b = b.dropna(subset=[date_col, name_col, value_col])
    b = b[b[value_col] > 0]
    b = b.sort_values([name_col, date_col])
    b = b.drop_duplicates([name_col, date_col])

    b["benchmark_return"] = b.groupby(name_col)[value_col].pct_change()

    return b.rename(
        columns={
            date_col: "date",
            name_col: "benchmark_name",
            value_col: "benchmark_value",
        }
    )


def choose_benchmark_name(names: pd.Series, keyword: str) -> str | None:
    """Find a benchmark name containing a keyword, case-insensitively."""
    matches = names[names.str.contains(keyword, case=False, na=False)].unique()
    return str(matches[0]) if len(matches) else None


# ---------------------------------------------------------------------
# Main analytics
# ---------------------------------------------------------------------

def main() -> None:
    """Run the complete performance analytics pipeline."""
    logger.info("Starting performance analytics.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not NAV_FILE.exists():
        raise FileNotFoundError(f"NAV file not found: {NAV_FILE}")

    nav = normalize_columns(pd.read_csv(NAV_FILE))

    require_columns(
        nav,
        ["date", "amfi_code", "nav", "scheme_name"],
        "NAV history",
    )

    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    nav["amfi_code"] = pd.to_numeric(nav["amfi_code"], errors="coerce")
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")

    nav = nav.dropna(subset=["date", "amfi_code", "nav"])
    nav = nav[nav["nav"] > 0]
    nav = nav.sort_values(["amfi_code", "date"])
    nav = nav.drop_duplicates(["amfi_code", "date"], keep="last")

    logger.info(
        "Loaded %s NAV observations for %s schemes.",
        f"{len(nav):,}",
        nav["amfi_code"].nunique(),
    )

    # -------------------------------------------------------------
    # 1. Daily returns
    # -------------------------------------------------------------

    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

    daily_returns = nav[
        ["date", "amfi_code", "scheme_name", "nav", "daily_return"]
    ].copy()

    daily_returns.to_csv(OUTPUT_DAILY_RETURNS, index=False)

    logger.info("Saved daily returns: %s", OUTPUT_DAILY_RETURNS)

    # -------------------------------------------------------------
    # 2. Performance metrics per fund
    # -------------------------------------------------------------

    performance_rows = []

    for code, group in nav.groupby("amfi_code", sort=False):
        group = group.sort_values("date").copy()
        returns = group["daily_return"].dropna()

        max_dd, max_dd_date = calculate_max_drawdown(group["nav"])

        row = {
            "amfi_code": int(code),
            "scheme_name": group["scheme_name"].iloc[-1],
            "start_date": group["date"].min(),
            "end_date": group["date"].max(),
            "observations": len(group),
            "return_1yr_cagr_pct": calculate_cagr(group["nav"], TRADING_DAYS) * 100,
            "return_3yr_cagr_pct": calculate_cagr(group["nav"], 3 * TRADING_DAYS) * 100,
            "return_5yr_cagr_pct": calculate_cagr(group["nav"], 5 * TRADING_DAYS) * 100,
            "sharpe_ratio": calculate_sharpe(returns),
            "sortino_ratio": calculate_sortino(returns),
            "max_drawdown_pct": max_dd * 100,
            "max_drawdown_date": max_dd_date,
            "annualised_volatility_pct": returns.std(ddof=1) * np.sqrt(TRADING_DAYS) * 100,
        }

        performance_rows.append(row)

    metrics = pd.DataFrame(performance_rows)

    # -------------------------------------------------------------
    # 3. Alpha / Beta against Nifty 100
    # -------------------------------------------------------------

    if BENCHMARK_FILE.exists():
        benchmark = normalize_columns(pd.read_csv(BENCHMARK_FILE))
        b_returns = benchmark_returns(benchmark)

        nifty100_name = choose_benchmark_name(
            b_returns["benchmark_name"],
            "Nifty.*100|Nifty 100",
        )

        if nifty100_name:
            nifty100 = b_returns[
                b_returns["benchmark_name"] == nifty100_name
            ][["date", "benchmark_return"]].copy()

            alpha_beta_rows = []

            for code, group in nav.groupby("amfi_code", sort=False):
                fund = group[["date", "daily_return"]].dropna()

                merged = fund.merge(nifty100, on="date", how="inner")
                merged = merged.replace([np.inf, -np.inf], np.nan).dropna()

                if len(merged) >= 30:
                    regression = linregress(
                        merged["benchmark_return"],
                        merged["daily_return"],
                    )

                    beta = regression.slope
                    alpha_daily = regression.intercept
                    alpha_annual = alpha_daily * TRADING_DAYS

                    alpha_beta_rows.append(
                        {
                            "amfi_code": int(code),
                            "scheme_name": group["scheme_name"].iloc[-1],
                            "alpha_annual_pct": alpha_annual * 100,
                            "beta": beta,
                            "r_squared": regression.rvalue ** 2,
                            "benchmark": nifty100_name,
                            "regression_observations": len(merged),
                        }
                    )
                else:
                    alpha_beta_rows.append(
                        {
                            "amfi_code": int(code),
                            "scheme_name": group["scheme_name"].iloc[-1],
                            "alpha_annual_pct": np.nan,
                            "beta": np.nan,
                            "r_squared": np.nan,
                            "benchmark": nifty100_name,
                            "regression_observations": len(merged),
                        }
                    )

            alpha_beta = pd.DataFrame(alpha_beta_rows)

        else:
            logger.warning(
                "Nifty 100 was not found in benchmark data. "
                "Alpha/Beta will be saved as empty."
            )
            alpha_beta = pd.DataFrame(
                columns=[
                    "amfi_code",
                    "scheme_name",
                    "alpha_annual_pct",
                    "beta",
                    "r_squared",
                    "benchmark",
                    "regression_observations",
                ]
            )
    else:
        logger.warning("Benchmark file not found: %s", BENCHMARK_FILE)
        alpha_beta = pd.DataFrame(
            columns=[
                "amfi_code",
                "scheme_name",
                "alpha_annual_pct",
                "beta",
                "r_squared",
                "benchmark",
                "regression_observations",
            ]
        )

    alpha_beta.to_csv(OUTPUT_ALPHA_BETA, index=False)

    metrics = metrics.merge(
        alpha_beta[
            ["amfi_code", "alpha_annual_pct", "beta", "r_squared"]
        ],
        on="amfi_code",
        how="left",
    )

    # -------------------------------------------------------------
    # 4. Merge scheme metadata
    # -------------------------------------------------------------

    if PERFORMANCE_FILE.exists():
        performance = normalize_columns(pd.read_csv(PERFORMANCE_FILE))

        require_columns(
            performance,
            ["amfi_code"],
            "Scheme performance",
        )

        performance["amfi_code"] = pd.to_numeric(
            performance["amfi_code"],
            errors="coerce",
        )

        metadata_columns = [
            col
            for col in [
                "fund_house",
                "category",
                "plan",
                "expense_ratio_pct",
                "risk_grade",
                "aum_crore",
                "morningstar_rating",
            ]
            if col in performance.columns
        ]

        if metadata_columns:
            metadata = performance[
                ["amfi_code"] + metadata_columns
            ].drop_duplicates("amfi_code")

            metrics = metrics.merge(
                metadata,
                on="amfi_code",
                how="left",
            )

    # -------------------------------------------------------------
    # 5. Fund Scorecard — 0 to 100
    # -------------------------------------------------------------

    # Higher is better for these metrics.
    metrics["rank_3yr_return"] = (
        metrics["return_3yr_cagr_pct"].rank(pct=True, ascending=True) * 100
    )

    metrics["rank_sharpe"] = (
        metrics["sharpe_ratio"].rank(pct=True, ascending=True) * 100
    )

    metrics["rank_alpha"] = (
        metrics["alpha_annual_pct"].rank(pct=True, ascending=True) * 100
    )

    # Lower expense ratio is better.
    if "expense_ratio_pct" in metrics.columns:
        metrics["rank_expense_inverse"] = (
            metrics["expense_ratio_pct"]
            .rank(pct=True, ascending=False)
            * 100
        )
    else:
        metrics["rank_expense_inverse"] = np.nan

    # Less negative drawdown / smaller absolute drawdown is better.
    metrics["rank_max_dd_inverse"] = (
        metrics["max_drawdown_pct"].abs()
        .rank(pct=True, ascending=False)
        * 100
    )

    metrics["fund_score"] = (
        0.30 * metrics["rank_3yr_return"]
        + 0.25 * metrics["rank_sharpe"]
        + 0.20 * metrics["rank_alpha"]
        + 0.15 * metrics["rank_expense_inverse"]
        + 0.10 * metrics["rank_max_dd_inverse"]
    )

    metrics["fund_rank"] = (
        metrics["fund_score"]
        .rank(ascending=False, method="min")
        .astype("Int64")
    )

    scorecard_columns = [
        "fund_rank",
        "fund_score",
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
        "plan",
        "return_1yr_cagr_pct",
        "return_3yr_cagr_pct",
        "return_5yr_cagr_pct",
        "sharpe_ratio",
        "sortino_ratio",
        "alpha_annual_pct",
        "beta",
        "annualised_volatility_pct",
        "max_drawdown_pct",
        "max_drawdown_date",
        "expense_ratio_pct",
        "aum_crore",
        "risk_grade",
    ]

    scorecard_columns = [
        col for col in scorecard_columns if col in metrics.columns
    ]

    scorecard = metrics[scorecard_columns].sort_values(
        "fund_rank",
        na_position="last",
    )

    scorecard.to_csv(OUTPUT_SCORECARD, index=False)

    logger.info("Saved fund scorecard: %s", OUTPUT_SCORECARD)
    logger.info("Funds scored: %s", len(scorecard))

    # -------------------------------------------------------------
    # 6. Benchmark comparison — top 5 funds vs Nifty 50 / Nifty 100
    # -------------------------------------------------------------

    if BENCHMARK_FILE.exists():
        benchmark = normalize_columns(pd.read_csv(BENCHMARK_FILE))
        b_returns = benchmark_returns(benchmark)

        nifty50_name = choose_benchmark_name(
            b_returns["benchmark_name"],
            "Nifty.*50|Nifty 50",
        )
        nifty100_name = choose_benchmark_name(
            b_returns["benchmark_name"],
            "Nifty.*100|Nifty 100",
        )

        if nifty50_name or nifty100_name:
            top5_codes = scorecard.head(5)["amfi_code"].tolist()

            end_date = nav["date"].max()
            start_date = end_date - pd.DateOffset(years=3)

            plt.figure(figsize=(14, 8))

            # Plot top 5 funds.
            for code in top5_codes:
                fund = nav[
                    (nav["amfi_code"] == code)
                    & (nav["date"] >= start_date)
                ][["date", "nav", "scheme_name"]].copy()

                if fund.empty:
                    continue

                fund["indexed"] = fund["nav"] / fund["nav"].iloc[0] * 100

                plt.plot(
                    fund["date"],
                    fund["indexed"],
                    linewidth=1.8,
                    label=fund["scheme_name"].iloc[0][:35],
                )

            # Plot benchmarks.
            benchmark_tracking = []

            for benchmark_name in [nifty50_name, nifty100_name]:
                if not benchmark_name:
                    continue

                b = b_returns[
                    (b_returns["benchmark_name"] == benchmark_name)
                    & (b_returns["date"] >= start_date)
                ].copy()

                if b.empty:
                    continue

                b["indexed"] = (
                    b["benchmark_value"]
                    / b["benchmark_value"].iloc[0]
                    * 100
                )

                plt.plot(
                    b["date"],
                    b["indexed"],
                    linestyle="--",
                    linewidth=2,
                    label=benchmark_name,
                )

                benchmark_tracking.append(benchmark_name)

            plt.title("Top 5 Funds vs Nifty Benchmarks — 3-Year Comparison")
            plt.xlabel("Date")
            plt.ylabel("Indexed Value (Base = 100)")
            plt.grid(alpha=0.25)
            plt.legend(fontsize=8, loc="best")
            plt.tight_layout()
            plt.savefig(
                OUTPUT_BENCHMARK_CHART,
                dpi=300,
                bbox_inches="tight",
            )
            plt.close()

            logger.info(
                "Saved benchmark comparison chart: %s",
                OUTPUT_BENCHMARK_CHART,
            )

            # Tracking error for top 5 vs available benchmarks.
            tracking_rows = []

            for code in top5_codes:
                fund = nav[
                    (nav["amfi_code"] == code)
                    & (nav["date"] >= start_date)
                ][["date", "daily_return", "scheme_name"]].dropna()

                for benchmark_name in benchmark_tracking:
                    b = b_returns[
                        (b_returns["benchmark_name"] == benchmark_name)
                        & (b_returns["date"] >= start_date)
                    ][["date", "benchmark_return"]].dropna()

                    merged = fund.merge(b, on="date", how="inner").dropna()

                    if len(merged) >= 30:
                        tracking_error = (
                            merged["daily_return"]
                            - merged["benchmark_return"]
                        ).std(ddof=1) * np.sqrt(TRADING_DAYS)

                        tracking_rows.append(
                            {
                                "amfi_code": int(code),
                                "scheme_name": fund["scheme_name"].iloc[0],
                                "benchmark": benchmark_name,
                                "tracking_error_annual_pct": tracking_error * 100,
                                "observations": len(merged),
                            }
                        )

            tracking_df = pd.DataFrame(tracking_rows)

            if not tracking_df.empty:
                tracking_path = PROCESSED_DIR / "tracking_error.csv"
                tracking_df.to_csv(tracking_path, index=False)
                logger.info("Saved tracking error: %s", tracking_path)

    logger.info("Performance analytics completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Performance analytics failed.")
        raise
