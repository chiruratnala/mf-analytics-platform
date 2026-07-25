"""
data_ingestion.py
------------------
Loads all 10 provided MF Analytics datasets from data/raw/, prints
shape / dtypes / head for each, and runs basic data-quality checks
(nulls, duplicates, unexpected dtypes) to build a short anomaly summary.

Usage:
    python data_ingestion.py
"""

import os
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 150)

RAW_DIR = os.path.join("data", "raw")

# Expected filenames -> friendly key name.
# Update the filenames on the right if yours differ.
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


def load_dataset(name: str, filename: str) -> pd.DataFrame | None:
    """Load a single CSV and print shape, dtypes, and head."""
    path = os.path.join(RAW_DIR, filename)

    if not os.path.exists(path):
        print(f"[MISSING] {name}: expected file not found at {path}")
        return None

    df = pd.read_csv(path)

    print("=" * 90)
    print(f"DATASET: {name}  ({filename})")
    print("=" * 90)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    print("Dtypes:")
    print(df.dtypes)
    print()

    print("Head:")
    print(df.head())
    print("\n")

    return df


def check_anomalies(name: str, df: pd.DataFrame) -> list[str]:
    """Run basic data-quality checks and return a list of findings."""
    findings = []

    # Nulls
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if not null_cols.empty:
        findings.append(
            f"- Missing values in columns: "
            + ", ".join(f"{col} ({cnt})" for col, cnt in null_cols.items())
        )

    # Duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        findings.append(f"- {dup_count} fully duplicate row(s) found.")

    # Columns that look like dates but are stored as text (object dtype)
    for col in df.columns:
        if "date" in col.lower() and df[col].dtype == "object":
            findings.append(
                f"- Column '{col}' looks like a date but is stored as text (object). "
                f"Convert with pd.to_datetime()."
            )

    # Columns that look numeric but are stored as text (e.g. amounts with commas/symbols)
    for col in df.columns:
        if df[col].dtype == "object":
            sample = df[col].dropna().astype(str).head(20)
            if sample.str.contains(r"[\d]").any() and sample.str.contains(r"[,\u20b9%]").any():
                findings.append(
                    f"- Column '{col}' may contain numeric values stored as text "
                    f"(commas / ₹ / % symbols). Clean before casting to numeric."
                )

    # Scheme code column sanity (common join key)
    code_cols = [c for c in df.columns if "code" in c.lower() or "scheme_id" in c.lower()]
    for col in code_cols:
        n_unique = df[col].nunique()
        n_total = len(df)
        if name == "fund_master" and n_unique != n_total:
            findings.append(
                f"- '{col}' in fund_master is not unique ({n_unique} unique vs {n_total} rows). "
                f"Expected one row per scheme."
            )

    if not findings:
        findings.append("- No major anomalies detected in basic checks.")

    return findings


def main():
    loaded = {}
    anomaly_report = {}

    for name, filename in DATASETS.items():
        df = load_dataset(name, filename)
        if df is not None:
            loaded[name] = df
            anomaly_report[name] = check_anomalies(name, df)

    # ---- Data Quality Summary ----
    print("#" * 90)
    print("DATA QUALITY SUMMARY")
    print("#" * 90)
    for name, findings in anomaly_report.items():
        print(f"\n{name}:")
        for f in findings:
            print(f"  {f}")

    missing = set(DATASETS.keys()) - set(loaded.keys())
    if missing:
        print(f"\n[!] Datasets not loaded (check filenames in data/raw/): {sorted(missing)}")

    print(f"\nSuccessfully loaded {len(loaded)}/{len(DATASETS)} datasets.")

    return loaded


if __name__ == "__main__":
    main()
