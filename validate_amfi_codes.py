"""
validate_amfi_codes.py
------------------------
Task 7: Validate AMFI codes across fund_master and nav_history.
- Confirm every code in fund_master exists in nav_history
- Confirm every code in nav_history exists in fund_master (orphan check)
- Check NAV record count / date coverage per scheme
- Write a short data quality summary

Usage:
    python validate_amfi_codes.py
"""

import os
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 150)

RAW_DIR = os.path.join("data", "raw")
FUND_MASTER_PATH = os.path.join(RAW_DIR, "01_fund_master.csv")
NAV_HISTORY_PATH = os.path.join(RAW_DIR, "02_nav_history.csv")


def main():
    fund_master = pd.read_csv(FUND_MASTER_PATH)
    nav_history = pd.read_csv(NAV_HISTORY_PATH)
    nav_history["date"] = pd.to_datetime(nav_history["date"], errors="coerce")

    fm_codes = set(fund_master["amfi_code"])
    nav_codes = set(nav_history["amfi_code"])

    print("=" * 90)
    print("AMFI CODE VALIDATION: fund_master <-> nav_history")
    print("=" * 90)
    print(f"fund_master: {len(fm_codes)} unique amfi_codes")
    print(f"nav_history: {len(nav_codes)} unique amfi_codes")
    print()

    # ---- Codes in fund_master but missing from nav_history ----
    missing_nav = fm_codes - nav_codes
    if missing_nav:
        print(f"[ISSUE] {len(missing_nav)} scheme(s) in fund_master have NO NAV history:")
        missing_df = fund_master[fund_master["amfi_code"].isin(missing_nav)][
            ["amfi_code", "scheme_name", "fund_house"]
        ]
        print(missing_df.to_string(index=False))
    else:
        print("[OK] Every scheme in fund_master has at least one NAV record in nav_history.")
    print()

    # ---- Codes in nav_history but missing from fund_master (orphans) ----
    orphan_codes = nav_codes - fm_codes
    if orphan_codes:
        orphan_row_count = nav_history[nav_history["amfi_code"].isin(orphan_codes)].shape[0]
        print(f"[ISSUE] {len(orphan_codes)} amfi_code(s) appear in nav_history but NOT in "
              f"fund_master ({orphan_row_count} orphan rows):")
        print(f"  Orphan codes: {sorted(orphan_codes)}")
    else:
        print("[OK] Every amfi_code in nav_history is a recognized scheme in fund_master.")
    print()

    # ---- NAV coverage per scheme (only for matched codes) ----
    print("=" * 90)
    print("NAV COVERAGE PER SCHEME (matched codes only)")
    print("=" * 90)
    matched_codes = fm_codes & nav_codes
    coverage = (
        nav_history[nav_history["amfi_code"].isin(matched_codes)]
        .groupby("amfi_code")
        .agg(
            nav_records=("date", "count"),
            first_date=("date", "min"),
            last_date=("date", "max"),
        )
        .reset_index()
        .merge(fund_master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
    )
    coverage = coverage[["amfi_code", "scheme_name", "nav_records", "first_date", "last_date"]]
    print(coverage.to_string(index=False))
    print()

    # Flag schemes with unusually low record counts (potential data gaps)
    median_records = coverage["nav_records"].median()
    low_coverage = coverage[coverage["nav_records"] < median_records * 0.5]
    if not low_coverage.empty:
        print(f"[FLAG] {len(low_coverage)} scheme(s) have NAV record counts well below the "
              f"median ({median_records:.0f}) — possible data gaps:")
        print(low_coverage.to_string(index=False))
    else:
        print(f"[OK] No scheme has unusually low NAV record counts (median = {median_records:.0f}).")
    print()

    # ---- Summary ----
    print("=" * 90)
    print("DATA QUALITY SUMMARY — AMFI CODE VALIDATION")
    print("=" * 90)
    print(f"- Total schemes in fund_master: {len(fm_codes)}")
    print(f"- Total unique schemes with NAV data: {len(nav_codes)}")
    print(f"- Schemes missing NAV history: {len(missing_nav)}")
    print(f"- Orphan NAV codes (no matching fund_master entry): {len(orphan_codes)}")
    print(f"- Matched & fully joinable schemes: {len(matched_codes)} "
          f"({len(matched_codes)/len(fm_codes)*100:.1f}% of fund_master)")
    print(f"- NAV date range overall: {nav_history['date'].min().date()} to "
          f"{nav_history['date'].max().date()}")
    print(f"- Median NAV records per scheme: {median_records:.0f}")


if __name__ == "__main__":
    main()
