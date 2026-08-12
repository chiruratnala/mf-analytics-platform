# Bluestock Python Script Cleanup

## Cleaned scripts

- `data_ingestion.py` — raw-data inspection and quality checks.
- `live_nav_fetch.py` — mfapi.in NAV fetcher.
- `validate_amfi_codes.py` — AMFI join and NAV coverage validation.
- `explore_fund_master.py` — fund-master metadata exploration.
- `compute_metrics.py` — performance/risk analytics; preserved from the supplied implementation.
- `recommender.py` — risk-grade-based top-fund recommender with CLI support.
- `run_pipeline.py` — master execution script.

## Standards applied

- Module, function, and public entry-point docstrings.
- `pathlib.Path` instead of string-based path construction.
- `logging` instead of ad-hoc `print()` debugging.
- Explicit input validation and clear exceptions.
- Deterministic pipeline order.
- CLI arguments are parsed centrally by each executable script.
- No debug `print()` statements remain in the cleaned scripts.

## Master execution

From the project root:

    python scripts/run_pipeline.py

Optional live NAV refresh:

    python scripts/run_pipeline.py --fetch-live

Optional risk-based recommendation:

    python scripts/run_pipeline.py --risk Moderate

## Important source note

The project materials available in this conversation contained the
`run_pipeline.py` reference and the other Python scripts listed above,
but did not contain the actual `etl_pipeline.py` source file. The master
runner therefore expects `scripts/etl_pipeline.py` to be supplied in the
project repository rather than silently inventing or replacing its ETL
business logic.

The project specification identifies `etl_pipeline.py` as the master ETL
script and describes its role as data cleaning and database loading.
