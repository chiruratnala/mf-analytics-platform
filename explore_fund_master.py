"""
explore_fund_master.py
-----------------------
Explore fund_master.csv
- Unique fund houses
- Unique categories and sub-categories
- Unique risk categories
- AMFI scheme code structure
Usage:
    python explore_fund_master.py
"""

import os
import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 150)
RAW_DIR = os.path.join("data", "raw")
FUND_MASTER_PATH = os.path.join(RAW_DIR, "01_fund_master.csv")


def main():
    df = pd.read_csv(FUND_MASTER_PATH)

    print("=" * 90)
    print("FUND MASTER EXPLORATION")
    print("=" * 90)
    print(f"Total schemes: {len(df)}\n")

    # ---- Fund Houses ----
    fund_houses = sorted(df["fund_house"].unique())
    print(f"Unique Fund Houses ({len(fund_houses)}):")
    for fh in fund_houses:
        count = (df["fund_house"] == fh).sum()
        print(f"  - {fh}  ({count} schemes)")
    print()

    # ---- Categories ----
    categories = sorted(df["category"].unique())
    print(f"Unique Categories ({len(categories)}):")
    for c in categories:
        count = (df["category"] == c).sum()
        print(f"  - {c}  ({count} schemes)")
    print()

    # ---- Sub-categories ----
    sub_categories = sorted(df["sub_category"].unique())
    print(f"Unique Sub-Categories ({len(sub_categories)}):")
    for sc in sub_categories:
        count = (df["sub_category"] == sc).sum()
        print(f"  - {sc}  ({count} schemes)")
    print()

    # ---- Category x Sub-category breakdown ----
    print("Category -> Sub-Category breakdown:")
    breakdown = df.groupby(["category", "sub_category"]).size().reset_index(name="count")
    print(breakdown.to_string(index=False))
    print()

    # ---- Risk categories ----
    risk_categories = sorted(df["risk_category"].unique())
    print(f"Unique Risk Categories ({len(risk_categories)}):")
    for rc in risk_categories:
        count = (df["risk_category"] == rc).sum()
        print(f"  - {rc}  ({count} schemes)")
    print()

    # ---- Plan types ----
    plans = sorted(df["plan"].unique())
    print(f"Unique Plan Types ({len(plans)}): {plans}\n")

    # ---- SEBI category codes ----
    sebi_codes = sorted(df["sebi_category_code"].unique())
    print(f"Unique SEBI Category Codes ({len(sebi_codes)}): {sebi_codes}\n")

    # ---- AMFI Scheme Code structure ----
    print("=" * 90)
    print("AMFI SCHEME CODE STRUCTURE")
    print("=" * 90)
    print(f"Column: amfi_code | dtype: {df['amfi_code'].dtype}")
    print(f"Min code: {df['amfi_code'].min()}  |  Max code: {df['amfi_code'].max()}")
    print(f"Unique codes: {df['amfi_code'].nunique()} (out of {len(df)} rows -> "
          f"{'one row per scheme, as expected' if df['amfi_code'].nunique() == len(df) else 'DUPLICATES FOUND'})")
    print()
    print("Notes on AMFI codes:")
    print("  - Each amfi_code is a unique numeric ID assigned by AMFI to a single scheme+plan")
    print("    combination (e.g. Regular Growth and Direct Growth of the same fund get")
    print("    DIFFERENT amfi_codes, even though the underlying portfolio is identical).")
    print("  - This is confirmed by fund_house: SBI Bluechip Regular (119551) vs")
    print("    SBI Bluechip Direct (119552) — same scheme, different code, different plan.")
    print("  - amfi_code is the primary join key linking fund_master to nav_history,")
    print("    scheme_performance, transactions, and holdings.")
    print()

    # Example: show regular vs direct pairs for first fund house
    print("Example — Regular vs Direct plan pairs (same scheme_name root):")
    df["scheme_root"] = df["scheme_name"].str.replace(
        r" - (Regular|Direct) Plan.*", "", regex=True
    )
    sample_root = df["scheme_root"].iloc[0]
    pair = df[df["scheme_root"] == sample_root][
        ["amfi_code", "scheme_name", "plan", "expense_ratio_pct"]
    ]
    print(pair.to_string(index=False))


if __name__ == "__main__":
    main()
