"""Run the Bluestock mutual-fund analytics pipeline end to end.

Execution order:
    1. Optional live NAV fetch
    2. Raw-data quality inspection
    3. ETL / cleaning / database load
    4. AMFI-code validation
    5. Fund-master exploration
    6. Performance analytics
    7. Optional risk-based recommendation

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --fetch-live
    python scripts/run_pipeline.py --risk Moderate
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def run_script(name: str, *args: str) -> None:
    """Execute a project script using the current Python interpreter."""
    script_path = SCRIPTS_DIR / name
    if not script_path.exists():
        raise FileNotFoundError(
            f"Required pipeline script not found: {script_path}"
        )

    command = [sys.executable, str(script_path), *args]
    logger.info("START  %s", name)
    result = subprocess.run(command, cwd=ROOT_DIR, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit code {result.returncode}."
        )
    logger.info("DONE   %s", name)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the pipeline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fetch-live",
        action="store_true",
        help="Fetch selected live NAV histories before ETL.",
    )
    parser.add_argument(
        "--risk",
        choices=["Low", "Moderate", "High"],
        help="Run the optional top-3 fund recommender.",
    )
    return parser.parse_args()


def main() -> None:
    """Run every available pipeline stage in deterministic order."""
    args = parse_args()

    logger.info("Bluestock MF analytics pipeline started.")

    if args.fetch_live:
        run_script("live_nav_fetch.py")
    else:
        logger.info("Live NAV fetch skipped; use --fetch-live to enable it.")

    # This is intentionally retained as a separate stage so raw-data
    # diagnostics run before transformation.
    run_script("data_ingestion.py")

    # The original project specification identifies etl_pipeline.py as
    # the master ETL/data-cleaning stage. It must be present in scripts/.
    run_script("etl_pipeline.py")

    run_script("validate_amfi_codes.py")
    run_script("explore_fund_master.py")
    run_script("compute_metrics.py")

    if args.risk:
        run_script("recommender.py", "--risk", args.risk)

    logger.info("Bluestock MF analytics pipeline completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Pipeline failed.")
        raise SystemExit(1)
