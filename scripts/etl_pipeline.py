"""Day 2 ETL pipeline: clean all 10 raw Bluestock MF datasets.

The script reads data/raw/*.csv and writes cleaned files to data/processed/.
It uses pathlib-based paths, explicit validation, deterministic cleaning rules,
and writes a machine-readable ETL quality report to reports/etl_quality_report.csv.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
REPORT_DIR = ROOT_DIR / "reports"

DATASETS = {
    "fund_master": "01_fund_master.csv",
    "nav_history": "02_nav_history.csv",
    "aum": "03_aum_by_fund_house.csv",
    "sip": "04_monthly_sip_inflows.csv",
    "category_inflows": "05_category_inflows.csv",
    "folio": "06_industry_folio_count.csv",
    "performance": "07_scheme_performance.csv",
    "transactions": "08_investor_transactions.csv",
    "holdings": "09_portfolio_holdings.csv",
    "benchmark": "10_benchmark_indices.csv",
}

OUTPUTS = {
    key: PROCESSED_DIR / filename.replace(".csv", "_cleaned.csv")
    for key, filename in DATASETS.items()
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------- generic helpers ----------
def read_raw(key: str) -> pd.DataFrame:
    """Read one required raw CSV."""
    path = RAW_DIR / DATASETS[key]
    if not path.exists():
        raise FileNotFoundError(f"Missing raw dataset '{key}': {path}")
    return pd.read_csv(path)


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from string columns without changing business values."""
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype("string").str.strip()
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse columns whose names contain 'date' or are known month/date fields."""
    df = df.copy()
    for col in df.columns:
        if "date" in col.lower() or col.lower() in {"month", "year_month"}:
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def numeric_clean(series: pd.Series) -> pd.Series:
    """Convert currency/percentage-like strings to numeric values."""
    return pd.to_numeric(
        series.astype("string").str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.replace("%", "", regex=False).str.strip(),
        errors="coerce",
    )


def clean_generic(df: pd.DataFrame) -> pd.DataFrame:
    """Apply safe generic cleaning to supporting datasets."""
    df = clean_text_columns(df)
    df = parse_dates(df)
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def save(df: pd.DataFrame, key: str) -> int:
    """Write a cleaned CSV and return its row count."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS[key]
    output = df.copy()
    for col in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[col]):
            output[col] = output[col].dt.strftime("%Y-%m-%d")
    output.to_csv(path, index=False)
    return len(output)


# ---------- dataset-specific cleaners ----------
def clean_fund_master(df: pd.DataFrame) -> pd.DataFrame:
    """Clean fund master and enforce one row per AMFI code."""
    required = {"amfi_code", "scheme_name"}
    if missing := required - set(df.columns):
        raise ValueError(f"fund_master missing columns: {sorted(missing)}")
    df = clean_generic(df)
    df["amfi_code"] = numeric_clean(df["amfi_code"]).astype("Int64")
    if "launch_date" in df.columns:
        df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    numeric_cols = [c for c in ["expense_ratio_pct", "exit_load_pct", "min_sip_amount", "min_lumpsum_amount"] if c in df.columns]
    for col in numeric_cols:
        df[col] = numeric_clean(df[col])
    df = df.dropna(subset=["amfi_code"]).drop_duplicates(subset=["amfi_code"], keep="last")
    return df.reset_index(drop=True)


def clean_nav(df: pd.DataFrame) -> pd.DataFrame:
    """Clean NAV, remove duplicate observations, validate positive NAV and forward-fill calendar gaps."""
    required = {"date", "amfi_code", "nav"}
    if missing := required - set(df.columns):
        raise ValueError(f"nav_history missing columns: {sorted(missing)}")

    df = clean_text_columns(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amfi_code"] = numeric_clean(df["amfi_code"]).astype("Int64")
    df["nav"] = numeric_clean(df["nav"])
    df = df.dropna(subset=["date", "amfi_code", "nav"])
    df = df[df["nav"] > 0]
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="last")
    df = df.sort_values(["amfi_code", "date"])

    # The project specification requires a full calendar and forward-fill for
    # weekends/holidays. The fill is performed separately for each scheme.
    pieces: list[pd.DataFrame] = []
    for code, group in df.groupby("amfi_code", sort=False):
        group = group.set_index("date")[["nav"]]
        full_index = pd.date_range(group.index.min(), group.index.max(), freq="D")
        filled = group.reindex(full_index).ffill()
        filled.index.name = "date"
        filled["amfi_code"] = int(code)
        pieces.append(filled.reset_index())

    result = pd.concat(pieces, ignore_index=True)
    result = result[["date", "amfi_code", "nav"]].sort_values(["amfi_code", "date"]).reset_index(drop=True)
    if (result["nav"] <= 0).any() or result["nav"].isna().any():
        raise ValueError("NAV validation failed after cleaning")
    return result


def normalize_transaction_type(value: object) -> str | pd.NA:
    """Map common transaction-type spellings to SIP/Lumpsum/Redemption."""
    if pd.isna(value):
        return pd.NA
    key = re.sub(r"[^a-z]", "", str(value).lower())
    mapping = {
        "sip": "SIP",
        "systematicinvestmentplan": "SIP",
        "lumpsum": "Lumpsum",
        "lump": "Lumpsum",
        "oneTime": "Lumpsum",
        "onetime": "Lumpsum",
        "redemption": "Redemption",
        "redeem": "Redemption",
        "withdrawal": "Redemption",
    }
    return mapping.get(key, str(value).strip())


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise transaction types, dates, positive amounts and KYC enums."""
    required = {"transaction_date", "transaction_type", "amount_inr", "kyc_status"}
    if missing := required - set(df.columns):
        raise ValueError(f"transactions missing columns: {sorted(missing)}")
    df = clean_text_columns(df)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount_inr"] = numeric_clean(df["amount_inr"])
    df["transaction_type"] = df["transaction_type"].map(normalize_transaction_type)
    df["kyc_status"] = df["kyc_status"].str.strip().str.title()

    allowed_tx = {"SIP", "Lumpsum", "Redemption"}
    allowed_kyc = {"Verified", "Pending"}
    bad_tx = sorted(set(df["transaction_type"].dropna()) - allowed_tx)
    bad_kyc = sorted(set(df["kyc_status"].dropna()) - allowed_kyc)
    if bad_tx:
        raise ValueError(f"Unexpected transaction_type values: {bad_tx}")
    if bad_kyc:
        raise ValueError(f"Unexpected kyc_status values: {bad_kyc}")

    df = df.dropna(subset=["transaction_date", "transaction_type", "amount_inr"])
    df = df[df["amount_inr"] > 0]
    return df.drop_duplicates().sort_values("transaction_date").reset_index(drop=True)


def clean_performance(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Clean performance metrics and report anomalies without silently deleting them."""
    required = {"amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "expense_ratio_pct"}
    if missing := required - set(df.columns):
        raise ValueError(f"performance missing columns: {sorted(missing)}")
    df = clean_text_columns(df)
    numeric_cols = [c for c in df.columns if c.endswith("_pct") or c in {"amfi_code", "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct", "aum_crore", "morningstar_rating"}]
    for col in numeric_cols:
        df[col] = numeric_clean(df[col])

    anomalies: list[str] = []
    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]:
        invalid = df[col].isna().sum()
        if invalid:
            anomalies.append(f"{col}: {invalid} non-numeric/missing value(s)")
    expense = df["expense_ratio_pct"]
    out_of_range = ((expense < 0.1) | (expense > 2.5)).sum()
    if out_of_range:
        anomalies.append(f"expense_ratio_pct: {out_of_range} value(s) outside 0.1%-2.5%")
    df = df.drop_duplicates(subset=["amfi_code"], keep="last").reset_index(drop=True)
    return df, anomalies


def clean_supporting(key: str, df: pd.DataFrame) -> pd.DataFrame:
    """Clean non-specialised datasets using safe type/date/duplicate rules."""
    df = clean_generic(df)
    for col in df.columns:
        name = col.lower()
        if any(token in name for token in ["amount", "aum", "inflow", "weight", "value", "price", "return", "ratio", "percent", "pct"]):
            # Do not force IDs or categorical columns to numeric.
            if not any(token in name for token in ["code", "id", "year"]):
                converted = numeric_clean(df[col])
                if converted.notna().sum() >= max(1, int(len(df) * 0.8)):
                    df[col] = converted
    return df.reset_index(drop=True)


def run() -> pd.DataFrame:
    """Execute the full cleaning pipeline and return its quality report."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_rows: list[dict[str, object]] = []

    for key in DATASETS:
        source = read_raw(key)
        source_rows = len(source)
        anomalies: list[str] = []

        if key == "fund_master":
            cleaned = clean_fund_master(source)
        elif key == "nav_history":
            cleaned = clean_nav(source)
        elif key == "transactions":
            cleaned = clean_transactions(source)
        elif key == "performance":
            cleaned, anomalies = clean_performance(source)
        else:
            cleaned = clean_supporting(key, source)

        output_rows = save(cleaned, key)
        report_rows.append({
            "dataset": key,
            "source_rows": source_rows,
            "cleaned_rows": output_rows,
            "rows_removed_or_added": output_rows - source_rows,
            "anomalies": " | ".join(anomalies) if anomalies else "None detected",
            "output_file": str(OUTPUTS[key].relative_to(ROOT_DIR)),
        })
        logger.info("%-20s %8d -> %8d rows", key, source_rows, output_rows)

    report = pd.DataFrame(report_rows)
    report.to_csv(REPORT_DIR / "etl_quality_report.csv", index=False)
    logger.info("ETL completed. Quality report: %s", REPORT_DIR / "etl_quality_report.csv")
    return report


if __name__ == "__main__":
    run()
