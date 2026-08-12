"""Risk-based mutual-fund recommender using the cleaned performance dataset."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PERF_PATH = ROOT_DIR / "data" / "processed" / "07_scheme_performance_cleaned.csv"
RISK_MAP = {
    "Low": ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High": ["High", "Very High"],
}


def recommend_funds(risk_appetite: str, perf_path: str | Path = DEFAULT_PERF_PATH) -> pd.DataFrame:
    """Return up to three schemes with the highest Sharpe ratio for a risk appetite."""
    risk_appetite = risk_appetite.strip().title()
    if risk_appetite not in RISK_MAP:
        raise ValueError("risk_appetite must be Low, Moderate, or High")

    path = Path(perf_path)
    if not path.exists():
        raise FileNotFoundError(f"Performance dataset not found: {path}")

    perf = pd.read_csv(path)
    required = {"scheme_name", "fund_house", "risk_grade", "sharpe_ratio", "return_3yr_pct"}
    if missing := required - set(perf.columns):
        raise ValueError(f"Performance dataset missing columns: {sorted(missing)}")

    perf["sharpe_ratio"] = pd.to_numeric(perf["sharpe_ratio"], errors="coerce")
    matched = perf[perf["risk_grade"].isin(RISK_MAP[risk_appetite])].dropna(subset=["sharpe_ratio"])
    return matched.sort_values("sharpe_ratio", ascending=False).head(3).copy()


def main() -> None:
    """Run recommendations for all three supported risk appetites."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--risk", choices=list(RISK_MAP), help="Risk appetite to evaluate")
    parser.add_argument("--performance", type=Path, default=DEFAULT_PERF_PATH)
    args = parser.parse_args()

    appetites = [args.risk] if args.risk else list(RISK_MAP)
    for appetite in appetites:
        result = recommend_funds(appetite, args.performance)
        print(f"\nTop 3 funds for '{appetite}' risk appetite:")
        if result.empty:
            print("No matching funds found.")
        else:
            print(result[["scheme_name", "fund_house", "risk_grade", "sharpe_ratio", "return_3yr_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
