"""Day 1 data ingestion and basic quality checks for the Bluestock MF capstone."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"

DATASETS = {
    "fund_master": "01_fund_master.csv",
    "nav_history": "02_nav_history.csv",
    "aum_by_fund_house": "03_aum_by_fund_house.csv",
    "monthly_sip": "04_monthly_sip_inflows.csv",
    "category_inflows": "05_category_inflows.csv",
    "folio_count": "06_industry_folio_count.csv",
    "scheme_performance": "07_scheme_performance.csv",
    "transactions": "08_investor_transactions.csv",
    "holdings": "09_portfolio_holdings.csv",
    "benchmark": "10_benchmark_indices.csv",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_dataset(name: str, filename: str) -> pd.DataFrame | None:
    """Load one CSV from data/raw and print basic profiling information."""
    path = RAW_DIR / filename
    if not path.exists():
        logger.warning("[%s] Missing: %s", name, path)
        return None

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        logger.error("[%s] Could not read %s: %s", name, path, exc)
        return None

    print("=" * 90)
    print(f"DATASET: {name} ({filename})")
    print("=" * 90)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print("\nDtypes:")
    print(df.dtypes)
    print("\nHead:")
    print(df.head())
    return df


def check_anomalies(name: str, df: pd.DataFrame) -> list[str]:
    """Run generic non-destructive data-quality checks."""
    findings: list[str] = []

    null_cols = df.isna().sum()
    null_cols = null_cols[null_cols > 0]
    if not null_cols.empty:
        findings.append(
            "Missing values: "
            + ", ".join(f"{col} ({count})" for col, count in null_cols.items())
        )

    duplicates = int(df.duplicated().sum())
    if duplicates:
        findings.append(f"Fully duplicate rows: {duplicates}")

    for col in df.columns:
        if "date" in col.lower() and df[col].dtype == "object":
            findings.append(f"Date-like column '{col}' is stored as text")

    if "amfi_code" in df.columns:
        numeric_codes = pd.to_numeric(df["amfi_code"], errors="coerce")
        if numeric_codes.isna().any():
            findings.append("amfi_code contains non-numeric or missing values")

    if not findings:
        findings.append("No major anomalies detected by generic checks")
    return findings


def main() -> Dict[str, pd.DataFrame]:
    """Load all available raw datasets and print a quality summary."""
    loaded: Dict[str, pd.DataFrame] = {}
    report: dict[str, list[str]] = {}

    for name, filename in DATASETS.items():
        df = load_dataset(name, filename)
        if df is not None:
            loaded[name] = df
            report[name] = check_anomalies(name, df)

    print("\n" + "#" * 90)
    print("DATA QUALITY SUMMARY")
    print("#" * 90)
    for name, findings in report.items():
        print(f"\n{name}:")
        for finding in findings:
            print(f"  - {finding}")

    missing = sorted(set(DATASETS) - set(loaded))
    if missing:
        print(f"\nMissing datasets: {missing}")
    print(f"\nSuccessfully loaded {len(loaded)}/{len(DATASETS)} datasets.")
    return loaded


if __name__ == "__main__":
    main()
