"""Inspect and validate the raw Bluestock mutual-fund datasets.

The script loads the ten project CSV datasets from ``data/raw/`` and
produces a structured data-quality summary. Console output is limited to
informational logging; no ad-hoc debug prints are used.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def load_dataset(name: str, filename: str) -> pd.DataFrame | None:
    """Load one raw CSV dataset and return it as a DataFrame.

    Args:
        name: Logical dataset name used in logs and reports.
        filename: CSV filename under ``data/raw``.

    Returns:
        The loaded DataFrame, or ``None`` when the expected file is absent.
    """
    path = RAW_DIR / filename
    if not path.exists():
        logger.warning("Missing dataset %s: %s", name, path)
        return None

    df = pd.read_csv(path)
    logger.info(
        "Loaded %-22s | %7d rows | %3d columns",
        name,
        len(df),
        len(df.columns),
    )
    return df


def check_anomalies(name: str, df: pd.DataFrame) -> list[str]:
    """Return basic data-quality findings for a dataset.

    Checks missing values, duplicate rows, date-like object columns,
    numeric-looking text columns, and uniqueness of scheme identifiers
    in the fund-master dataset.
    """
    findings: list[str] = []

    null_counts = df.isna().sum()
    null_cols = null_counts[null_counts > 0]
    if not null_cols.empty:
        findings.append(
            "Missing values: "
            + ", ".join(f"{col} ({count})" for col, count in null_cols.items())
        )

    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        findings.append(f"Fully duplicate rows: {duplicate_count}")

    for column in df.columns:
        if "date" in column.lower() and df[column].dtype == "object":
            findings.append(
                f"Date-like column '{column}' is stored as text."
            )

        if df[column].dtype == "object":
            sample = df[column].dropna().astype(str).head(20)
            if (
                not sample.empty
                and sample.str.contains(r"\d", regex=True).any()
                and sample.str.contains(r"[,\u20b9%]", regex=True).any()
            ):
                findings.append(
                    f"Column '{column}' may contain numeric values stored as text."
                )

    code_columns = [
        column
        for column in df.columns
        if "code" in column.lower() or "scheme_id" in column.lower()
    ]
    if name == "fund_master":
        for column in code_columns:
            if df[column].nunique(dropna=False) != len(df):
                findings.append(
                    f"'{column}' is not unique in fund_master; "
                    "expected one row per scheme."
                )

    if not findings:
        findings.append("No major anomalies detected in basic checks.")

    return findings


def run_quality_check() -> dict[str, list[str]]:
    """Load all available raw datasets and return their quality findings."""
    report: dict[str, list[str]] = {}
    loaded_count = 0

    for name, filename in DATASETS.items():
        df = load_dataset(name, filename)
        if df is None:
            continue
        loaded_count += 1
        report[name] = check_anomalies(name, df)

    logger.info("Loaded %d/%d configured datasets.", loaded_count, len(DATASETS))
    for name, findings in report.items():
        for finding in findings:
            level = logging.WARNING if not finding.startswith("No major") else logging.INFO
            logger.log(level, "%s | %s", name, finding)

    return report


def main() -> None:
    """Run the raw-data quality inspection."""
    run_quality_check()


if __name__ == "__main__":
    main()
