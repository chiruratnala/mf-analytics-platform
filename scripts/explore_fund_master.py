"""Explore the fund-master dataset and document its join-key structure."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
FUND_MASTER_PATH = RAW_DIR / "01_fund_master.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Raise a clear error when expected fund-master columns are missing."""
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing fund-master columns: {missing}")


def main() -> None:
    """Print fund-house, category, risk, plan and AMFI-code exploration."""
    if not FUND_MASTER_PATH.exists():
        raise FileNotFoundError(f"Fund master not found: {FUND_MASTER_PATH}")

    df = pd.read_csv(FUND_MASTER_PATH)
    require_columns(
        df,
        ["amfi_code", "fund_house", "scheme_name", "category", "sub_category",
         "plan", "risk_category", "sebi_category_code"],
    )

    print("=" * 90)
    print("FUND MASTER EXPLORATION")
    print("=" * 90)
    print(f"Rows: {len(df)} | Unique AMFI codes: {df['amfi_code'].nunique()}")

    for column, label in [
        ("fund_house", "Fund Houses"),
        ("category", "Categories"),
        ("sub_category", "Sub-Categories"),
        ("risk_category", "Risk Categories"),
        ("plan", "Plan Types"),
        ("sebi_category_code", "SEBI Category Codes"),
    ]:
        values = df[column].dropna().astype(str).value_counts().sort_index()
        print(f"\n{label} ({len(values)}):")
        print(values.to_string())

    print("\nCategory -> Sub-category breakdown:")
    print(df.groupby(["category", "sub_category"], dropna=False).size().reset_index(name="count").to_string(index=False))

    codes = pd.to_numeric(df["amfi_code"], errors="coerce")
    print("\nAMFI code checks:")
    print(f"  Numeric codes: {codes.notna().sum()}/{len(df)}")
    print(f"  Unique codes: {df['amfi_code'].nunique()}")
    print(f"  Duplicate codes: {df['amfi_code'].duplicated().sum()}")
    print("  AMFI code is the primary join key across scheme-level datasets.")


if __name__ == "__main__":
    main()
