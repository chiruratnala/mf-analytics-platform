"""Fetch live NAV history for the six required schemes from mfapi.in."""
from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
BASE_URL = "https://api.mfapi.in/mf/{scheme_code}"

SCHEMES = {
    125497: "hdfc_top_100_direct",
    119551: "sbi_bluechip",
    120503: "icici_bluechip",
    118632: "nippon_large_cap",
    119092: "axis_bluechip",
    120841: "kotak_bluechip",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def fetch_scheme_nav(scheme_code: int, retries: int = 3) -> dict:
    """Fetch and validate one mfapi.in response."""
    url = BASE_URL.format(scheme_code=scheme_code)
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not payload.get("data"):
                raise ValueError("API response contains no NAV data")
            return payload
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            logger.warning("Attempt %d/%d failed for %s: %s", attempt, retries, scheme_code, exc)
            if attempt < retries:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Unable to fetch scheme {scheme_code}: {last_error}")


def save_scheme_nav(scheme_code: int, friendly_name: str) -> pd.DataFrame:
    """Fetch, clean and save one scheme's NAV history."""
    payload = fetch_scheme_nav(scheme_code)
    meta = payload.get("meta", {}) or {}
    df = pd.DataFrame(payload["data"])

    required = {"date", "nav"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Scheme {scheme_code}: missing API columns {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["amfi_code"] = scheme_code
    df["scheme_name"] = meta.get("scheme_name", friendly_name)
    df["fund_house"] = meta.get("fund_house", "")

    df = df.dropna(subset=["date", "nav"])
    df = df[df["nav"] > 0]
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)
    df = df[["amfi_code", "scheme_name", "fund_house", "date", "nav"]]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output = RAW_DIR / f"live_nav_{friendly_name}.csv"
    df.to_csv(output, index=False, date_format="%Y-%m-%d")
    logger.info("Saved %s rows to %s", len(df), output)
    return df


def main() -> None:
    """Fetch all configured schemes; continue after an individual failure."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    success = 0
    for code, name in SCHEMES.items():
        try:
            save_scheme_nav(code, name)
            success += 1
        except Exception as exc:
            logger.error("Failed scheme %s: %s", code, exc)
        time.sleep(1)
    logger.info("Successfully fetched %d/%d schemes.", success, len(SCHEMES))


if __name__ == "__main__":
    main()
