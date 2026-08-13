"""Summarise the structure of the mutual-fund master dataset."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FUND_MASTER_PATH = PROJECT_ROOT / "data" / "raw" / "01_fund_master.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def load_fund_master(path: Path = FUND_MASTER_PATH) -> pd.DataFrame:
    """Load the fund-master CSV after validating that it exists."""
    if not path.exists():
        raise FileNotFoundError(f"Fund-master file not found: {path}")
    return pd.read_csv(path)


def build_summary(df: pd.DataFrame) -> dict[str, object]:
    """Build reusable fund-master summary information."""
    required = {
        "fund_house",
        "category",
        "sub_category",
        "risk_category",
        "plan",
        "sebi_category_code",
        "amfi_code",
        "scheme_name",
        "expense_ratio_pct",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"fund_master is missing required columns: {missing}")

    return {
        "total_schemes": len(df),
        "fund_houses": sorted(df["fund_house"].dropna().unique().tolist()),
        "categories": sorted(df["category"].dropna().unique().tolist()),
        "sub_categories": sorted(df["sub_category"].dropna().unique().tolist()),
        "risk_categories": sorted(df["risk_category"].dropna().unique().tolist()),
        "plans": sorted(df["plan"].dropna().unique().tolist()),
        "sebi_codes": sorted(df["sebi_category_code"].dropna().unique().tolist()),
        "min_amfi_code": df["amfi_code"].min(),
        "max_amfi_code": df["amfi_code"].max(),
        "unique_amfi_codes": int(df["amfi_code"].nunique()),
    }


def log_summary(df: pd.DataFrame, summary: dict[str, object]) -> None:
    """Write the fund-master summary through the project logger."""
    logger.info("Total schemes: %s", summary["total_schemes"])
    logger.info(
        "Fund houses: %d | Categories: %d | Sub-categories: %d",
        len(summary["fund_houses"]),
        len(summary["categories"]),
        len(summary["sub_categories"]),
    )
    logger.info(
        "Risk categories: %s | Plans: %s",
        ", ".join(summary["risk_categories"]),
        ", ".join(summary["plans"]),
    )
    logger.info(
        "AMFI code range: %s–%s | unique codes: %s",
        summary["min_amfi_code"],
        summary["max_amfi_code"],
        summary["unique_amfi_codes"],
    )

    breakdown = (
        df.groupby(["category", "sub_category"])
        .size()
        .reset_index(name="count")
    )
    logger.info("Category/sub-category breakdown:\n%s", breakdown.to_string(index=False))

    if summary["unique_amfi_codes"] != summary["total_schemes"]:
        logger.warning("AMFI codes are not unique in fund_master.")

    scheme_root = df["scheme_name"].astype(str).str.replace(
        r" - (Regular|Direct) Plan.*",
        "",
        regex=True,
    )
    first_root = scheme_root.iloc[0]
    pair = df.loc[
        scheme_root.eq(first_root),
        ["amfi_code", "scheme_name", "plan", "expense_ratio_pct"],
    ]
    logger.info("Example Regular/Direct pair:\n%s", pair.to_string(index=False))


def main() -> None:
    """Load and report fund-master metadata."""
    df = load_fund_master()
    summary = build_summary(df)
    log_summary(df, summary)


if __name__ == "__main__":
    main()
