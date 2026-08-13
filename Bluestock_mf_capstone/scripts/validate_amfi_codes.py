"""Validate AMFI-code consistency and NAV coverage."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FUND_MASTER_PATH = RAW_DIR / "01_fund_master.csv"
NAV_HISTORY_PATH = RAW_DIR / "02_nav_history.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def validate_amfi_codes(
    fund_master_path: Path = FUND_MASTER_PATH,
    nav_history_path: Path = NAV_HISTORY_PATH,
) -> dict[str, object]:
    """Validate fund-master/NAV joins and return a machine-readable summary."""
    for path in (fund_master_path, nav_history_path):
        if not path.exists():
            raise FileNotFoundError(f"Required input file not found: {path}")

    fund_master = pd.read_csv(fund_master_path)
    nav_history = pd.read_csv(nav_history_path)

    required_fund = {"amfi_code", "scheme_name", "fund_house"}
    required_nav = {"amfi_code", "date"}
    if missing := required_fund - set(fund_master.columns):
        raise ValueError(f"fund_master missing columns: {sorted(missing)}")
    if missing := required_nav - set(nav_history.columns):
        raise ValueError(f"nav_history missing columns: {sorted(missing)}")

    nav_history["date"] = pd.to_datetime(
        nav_history["date"],
        errors="coerce",
    )
    fund_codes = set(fund_master["amfi_code"].dropna())
    nav_codes = set(nav_history["amfi_code"].dropna())

    missing_nav = fund_codes - nav_codes
    orphan_codes = nav_codes - fund_codes
    matched_codes = fund_codes & nav_codes

    coverage = (
        nav_history[nav_history["amfi_code"].isin(matched_codes)]
        .groupby("amfi_code")
        .agg(
            nav_records=("date", "count"),
            first_date=("date", "min"),
            last_date=("date", "max"),
        )
        .reset_index()
        .merge(
            fund_master[["amfi_code", "scheme_name"]],
            on="amfi_code",
            how="left",
        )
    )

    median_records = (
        float(coverage["nav_records"].median())
        if not coverage.empty
        else 0.0
    )
    low_coverage = coverage[
        coverage["nav_records"] < median_records * 0.5
    ].copy() if median_records else coverage.iloc[0:0]

    result = {
        "fund_master_codes": len(fund_codes),
        "nav_codes": len(nav_codes),
        "missing_nav_codes": sorted(missing_nav),
        "orphan_codes": sorted(orphan_codes),
        "matched_codes": len(matched_codes),
        "coverage": coverage,
        "median_nav_records": median_records,
        "low_coverage": low_coverage,
        "nav_min_date": nav_history["date"].min(),
        "nav_max_date": nav_history["date"].max(),
    }
    return result


def main() -> None:
    """Run AMFI-code validation and log the quality summary."""
    result = validate_amfi_codes()

    if result["missing_nav_codes"]:
        logger.warning(
            "Schemes missing NAV history: %s",
            len(result["missing_nav_codes"]),
        )
    else:
        logger.info("All fund-master schemes have NAV history.")

    if result["orphan_codes"]:
        logger.warning(
            "Orphan NAV codes: %s",
            len(result["orphan_codes"]),
        )
    else:
        logger.info("No orphan NAV codes found.")

    if not result["low_coverage"].empty:
        logger.warning(
            "Low-coverage schemes: %s",
            len(result["low_coverage"]),
        )

    logger.info(
        "AMFI validation: %d fund-master codes | %d NAV codes | "
        "%d matched | %.0f median NAV records/scheme | "
        "date range %s to %s",
        result["fund_master_codes"],
        result["nav_codes"],
        result["matched_codes"],
        result["median_nav_records"],
        result["nav_min_date"].date() if pd.notna(result["nav_min_date"]) else "N/A",
        result["nav_max_date"].date() if pd.notna(result["nav_max_date"]) else "N/A",
    )


if __name__ == "__main__":
    main()
