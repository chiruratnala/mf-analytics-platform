"""Validate AMFI-code integrity and NAV coverage between fund master and NAV history."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
REPORT_DIR = ROOT_DIR / "reports"
FUND_MASTER_PATH = RAW_DIR / "01_fund_master.csv"
NAV_HISTORY_PATH = RAW_DIR / "02_nav_history.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    """Run join-key and coverage checks and write a text summary."""
    if not FUND_MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing: {FUND_MASTER_PATH}")
    if not NAV_HISTORY_PATH.exists():
        raise FileNotFoundError(f"Missing: {NAV_HISTORY_PATH}")

    fund_master = pd.read_csv(FUND_MASTER_PATH)
    nav = pd.read_csv(NAV_HISTORY_PATH)
    required_fm = {"amfi_code", "scheme_name", "fund_house"}
    required_nav = {"amfi_code", "date"}
    if missing := required_fm - set(fund_master.columns):
        raise ValueError(f"Fund master missing columns: {sorted(missing)}")
    if missing := required_nav - set(nav.columns):
        raise ValueError(f"NAV history missing columns: {sorted(missing)}")

    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    fm_codes = set(pd.to_numeric(fund_master["amfi_code"], errors="coerce").dropna().astype(int))
    nav_codes = set(pd.to_numeric(nav["amfi_code"], errors="coerce").dropna().astype(int))

    missing_nav = sorted(fm_codes - nav_codes)
    orphan_codes = sorted(nav_codes - fm_codes)
    matched = sorted(fm_codes & nav_codes)

    coverage = (
        nav[nav["amfi_code"].isin(matched)]
        .groupby("amfi_code")
        .agg(nav_records=("date", "count"), first_date=("date", "min"), last_date=("date", "max"))
        .reset_index()
        .merge(fund_master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
    )
    median_records = coverage["nav_records"].median() if not coverage.empty else 0
    low_coverage = coverage[coverage["nav_records"] < median_records * 0.5] if median_records else coverage.iloc[0:0]

    print("=" * 90)
    print("AMFI CODE VALIDATION")
    print("=" * 90)
    print(f"Fund-master codes: {len(fm_codes)}")
    print(f"NAV codes: {len(nav_codes)}")
    print(f"Missing NAV codes: {len(missing_nav)}")
    print(f"Orphan NAV codes: {len(orphan_codes)}")
    print(f"Matched codes: {len(matched)}")
    print(f"NAV date range: {nav['date'].min()} to {nav['date'].max()}")
    print(f"Median NAV records/scheme: {median_records:.0f}")
    if missing_nav:
        print("Missing codes:", missing_nav)
    if orphan_codes:
        print("Orphan codes:", orphan_codes)
    if not low_coverage.empty:
        print(f"Low-coverage schemes: {len(low_coverage)}")
        print(low_coverage.to_string(index=False))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = [
        f"Fund-master codes: {len(fm_codes)}",
        f"NAV codes: {len(nav_codes)}",
        f"Missing NAV codes: {len(missing_nav)}",
        f"Orphan NAV codes: {len(orphan_codes)}",
        f"Matched codes: {len(matched)}",
        f"NAV date range: {nav['date'].min()} to {nav['date'].max()}",
        f"Median NAV records/scheme: {median_records:.0f}",
    ]
    (REPORT_DIR / "amfi_validation_summary.txt").write_text("\n".join(summary), encoding="utf-8")
    coverage.to_csv(REPORT_DIR / "nav_coverage_by_scheme.csv", index=False)


if __name__ == "__main__":
    main()
