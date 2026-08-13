"""Fetch selected mutual-fund NAV histories from mfapi.in."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
BASE_URL = "https://api.mfapi.in/mf/{}"

SCHEMES = {
    125497: "hdfc_top_100_direct",
    119551: "sbi_bluechip",
    120503: "icici_bluechip",
    118632: "nippon_large_cap",
    119092: "axis_bluechip",
    120841: "kotak_bluechip",
}

REQUEST_TIMEOUT = 15
REQUEST_DELAY_SECONDS = 1.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_scheme_nav(
    scheme_code: int,
    session: requests.Session | None = None,
) -> dict | None:
    """Fetch and validate the JSON response for one AMFI scheme code."""
    client = session or requests.Session()
    url = BASE_URL.format(scheme_code)

    try:
        response = client.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.error("Failed to fetch scheme %s: %s", scheme_code, exc)
        return None

    if payload.get("status") == "SUCCESS" or "data" in payload:
        return payload

    logger.warning("Unexpected API response for scheme %s.", scheme_code)
    return None


def save_scheme_nav(
    scheme_code: int,
    friendly_name: str,
    session: requests.Session | None = None,
) -> pd.DataFrame | None:
    """Fetch one scheme's NAV history and save it to ``data/raw``."""
    payload = fetch_scheme_nav(scheme_code, session=session)
    if payload is None:
        return None

    records = payload.get("data", [])
    if not records:
        logger.warning("No NAV records returned for scheme %s.", scheme_code)
        return None

    metadata = payload.get("meta", {})
    df = pd.DataFrame(records)
    required = {"date", "nav"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"NAV response for {scheme_code} is missing columns: {sorted(missing)}"
        )

    df["amfi_code"] = scheme_code
    df["scheme_name"] = metadata.get("scheme_name", friendly_name)
    df["fund_house"] = metadata.get("fund_house", "")
    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y",
        errors="coerce",
    )
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = (
        df[["amfi_code", "scheme_name", "fund_house", "date", "nav"]]
        .dropna(subset=["date", "nav"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / f"live_nav_{friendly_name}.csv"
    df.to_csv(output_path, index=False)
    logger.info(
        "Saved %d NAV records for %s to %s.",
        len(df),
        friendly_name,
        output_path,
    )
    return df


def fetch_all_schemes() -> dict[str, pd.DataFrame]:
    """Fetch all configured schemes with a short delay between requests."""
    results: dict[str, pd.DataFrame] = {}
    with requests.Session() as session:
        for scheme_code, friendly_name in SCHEMES.items():
            df = save_scheme_nav(
                scheme_code,
                friendly_name,
                session=session,
            )
            if df is not None:
                results[friendly_name] = df
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(
        "Completed live NAV fetch: %d/%d schemes.",
        len(results),
        len(SCHEMES),
    )
    return results


def main() -> None:
    """Run the live NAV fetch for all configured schemes."""
    fetch_all_schemes()


if __name__ == "__main__":
    main()
