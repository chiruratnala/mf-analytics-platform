"""
live_nav_fetch.py
------------------
Fetches live NAV history from the mfapi.in public REST API for key
mutual fund schemes and saves each as a raw CSV in data/raw/.

API docs: https://www.mfapi.in/
Endpoint: https://api.mfapi.in/mf/<scheme_code>

Usage:
    python live_nav_fetch.py
"""

import os
import time
import requests
import pandas as pd

RAW_DIR = os.path.join("data", "raw")
BASE_URL = "https://api.mfapi.in/mf/{}"

# Scheme code -> friendly name (used for the output filename)
SCHEMES = {
    125497: "hdfc_top_100_direct",
    119551: "sbi_bluechip",
    120503: "icici_bluechip",
    118632: "nippon_large_cap",
    119092: "axis_bluechip",
    120841: "kotak_bluechip",
}


def fetch_scheme_nav(scheme_code: int) -> dict | None:
    """Call mfapi.in for a single scheme code and return the parsed JSON."""
    url = BASE_URL.format(scheme_code)
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "SUCCESS" or "data" in data:
            return data
        else:
            print(f"[WARN] Unexpected response for {scheme_code}: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch scheme {scheme_code}: {e}")
        return None


def save_scheme_nav(scheme_code: int, friendly_name: str) -> pd.DataFrame | None:
    """Fetch NAV history for one scheme and save it as a raw CSV."""
    print(f"Fetching scheme {scheme_code} ({friendly_name})...")

    payload = fetch_scheme_nav(scheme_code)
    if payload is None:
        return None

    meta = payload.get("meta", {})
    nav_records = payload.get("data", [])

    if not nav_records:
        print(f"[WARN] No NAV records returned for {scheme_code}")
        return None

    df = pd.DataFrame(nav_records)  # columns: date, nav
    df["amfi_code"] = scheme_code
    df["scheme_name"] = meta.get("scheme_name", friendly_name)
    df["fund_house"] = meta.get("fund_house", "")

    # Reorder columns
    df = df[["amfi_code", "scheme_name", "fund_house", "date", "nav"]]

    # Convert date to proper datetime and sort oldest -> newest
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    out_path = os.path.join(RAW_DIR, f"live_nav_{friendly_name}.csv")
    df.to_csv(out_path, index=False)

    print(f"  -> Saved {len(df)} NAV records to {out_path}")
    print(f"     Date range: {df['date'].min().date()} to {df['date'].max().date()}\n")

    return df


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    results = {}

    for code, name in SCHEMES.items():
        df = save_scheme_nav(code, name)
        if df is not None:
            results[name] = df
        time.sleep(1)  # be polite to the free public API

    print("=" * 60)
    print(f"Successfully fetched {len(results)}/{len(SCHEMES)} schemes.")
    for name, df in results.items():
        print(f"  - {name}: {len(df)} records")


if __name__ == "__main__":
    main()
