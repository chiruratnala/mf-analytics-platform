"""Rank mutual funds by Sharpe ratio for a selected risk appetite."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PERFORMANCE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "07_scheme_performance_cleaned.csv"
)

RISK_MAP = {
    "Low": ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High": ["High", "Very High"],
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def recommend_funds(
    risk_appetite: str,
    perf_path: Path = DEFAULT_PERFORMANCE_PATH,
    top_n: int = 3,
) -> pd.DataFrame:
    """Return the highest-Sharpe funds matching the requested risk appetite.

    Args:
        risk_appetite: ``Low``, ``Moderate`` or ``High``.
        perf_path: Path to the cleaned scheme-performance CSV.
        top_n: Maximum number of recommendations to return.
    """
    if risk_appetite not in RISK_MAP:
        valid = ", ".join(RISK_MAP)
        raise ValueError(f"risk_appetite must be one of: {valid}")
    if top_n < 1:
        raise ValueError("top_n must be at least 1.")
    if not perf_path.exists():
        raise FileNotFoundError(f"Performance file not found: {perf_path}")

    performance = pd.read_csv(perf_path)
    required = {"risk_grade", "sharpe_ratio", "scheme_name", "fund_house"}
    missing = required - set(performance.columns)
    if missing:
        raise ValueError(
            f"Performance dataset is missing required columns: {sorted(missing)}"
        )

    matched = performance[
        performance["risk_grade"].isin(RISK_MAP[risk_appetite])
    ].copy()

    return matched.sort_values(
        "sharpe_ratio",
        ascending=False,
    ).head(top_n)


def main() -> None:
    """Parse CLI arguments and log the recommendation table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--risk",
        choices=sorted(RISK_MAP),
        default="Moderate",
        help="Investor risk appetite.",
    )
    parser.add_argument(
        "--performance-file",
        type=Path,
        default=DEFAULT_PERFORMANCE_PATH,
        help="Path to cleaned scheme-performance CSV.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=3,
        help="Number of funds to return.",
    )
    args = parser.parse_args()

    recommendations = recommend_funds(
        args.risk,
        perf_path=args.performance_file,
        top_n=args.top_n,
    )
    logger.info(
        "Top %d funds for '%s' risk appetite:\n%s",
        len(recommendations),
        args.risk,
        recommendations.to_string(index=False),
    )


if __name__ == "__main__":
    main()
