-- =============================================================================
-- MF Analytics Platform — SQLite Star Schema
-- Bluestock Fintech Capstone · Day 2
-- =============================================================================
-- Design notes:
--   - dim_fund and dim_date are DIMENSION tables (descriptive, low row count)
--   - fact_nav, fact_transactions, fact_performance, fact_aum are FACT tables
--     (measurable events/numbers, high row count, reference dimensions via FK)
--   - fact_performance is a point-in-time SNAPSHOT (one row per scheme), so it
--     links only to dim_fund, not dim_date.
--   - fact_aum is aggregated at fund_house level (not per-scheme), so it does
--     NOT have a foreign key into dim_fund — fund_house is stored as plain
--     text. This is a deliberate grain mismatch: AUM data from AMFI is only
--     published at the AMC level, not the individual scheme level.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- DIMENSION: dim_fund
-- One row per scheme (source: 01_fund_master.csv)
-- =============================================================================
DROP TABLE IF EXISTS dim_fund;
CREATE TABLE dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,               -- 'Regular' or 'Direct'
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- =============================================================================
-- DIMENSION: dim_date
-- One row per calendar date, pre-computed date parts for easy BI slicing.
-- Populated programmatically in etl_pipeline.py (not hand-written here).
-- =============================================================================
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_id         INTEGER PRIMARY KEY,   -- format: YYYYMMDD, e.g. 20220103
    full_date       DATE NOT NULL UNIQUE,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,      -- 1-4
    month           INTEGER NOT NULL,      -- 1-12
    month_name      TEXT NOT NULL,         -- 'January'
    day             INTEGER NOT NULL,      -- 1-31
    day_name        TEXT NOT NULL,         -- 'Monday'
    is_weekend      INTEGER NOT NULL,      -- 0 or 1
    is_month_end    INTEGER NOT NULL       -- 0 or 1
);

-- =============================================================================
-- FACT: fact_nav
-- One row per scheme per day (source: 02_nav_history_cleaned.csv)
-- Grain: amfi_code + date
-- =============================================================================
DROP TABLE IF EXISTS fact_nav;
CREATE TABLE fact_nav (
    nav_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL,
    date_id     INTEGER NOT NULL,
    nav         REAL NOT NULL CHECK (nav > 0),

    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id),
    UNIQUE (amfi_code, date_id)   -- prevents duplicate NAV entries for same scheme+day
);

-- =============================================================================
-- FACT: fact_transactions
-- One row per investor transaction (source: 08_investor_transactions_cleaned.csv)
-- Grain: individual transaction
-- =============================================================================
DROP TABLE IF EXISTS fact_transactions;
CREATE TABLE fact_transactions (
    transaction_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id          TEXT NOT NULL,
    amfi_code            INTEGER NOT NULL,
    date_id               INTEGER NOT NULL,
    transaction_type      TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr            INTEGER NOT NULL CHECK (amount_inr > 0),
    state                 TEXT,
    city                  TEXT,
    city_tier             TEXT,
    age_group             TEXT,
    gender                TEXT,
    annual_income_lakh    REAL,
    payment_mode          TEXT,
    kyc_status            TEXT,

    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id)
);

-- =============================================================================
-- FACT: fact_performance
-- One row per scheme — a point-in-time snapshot (source: 07_scheme_performance_cleaned.csv)
-- Grain: amfi_code (no date dimension — this is not a time series)
-- =============================================================================
DROP TABLE IF EXISTS fact_performance;
CREATE TABLE fact_performance (
    amfi_code            INTEGER PRIMARY KEY,
    return_1yr_pct       REAL,
    return_3yr_pct       REAL,
    return_5yr_pct       REAL,
    benchmark_3yr_pct    REAL,
    alpha                REAL,
    beta                 REAL,
    sharpe_ratio         REAL,
    sortino_ratio        REAL,
    std_dev_ann_pct      REAL,
    max_drawdown_pct     REAL CHECK (max_drawdown_pct <= 0),
    aum_crore            INTEGER,
    expense_ratio_pct    REAL CHECK (expense_ratio_pct BETWEEN 0.1 AND 2.5),
    morningstar_rating   INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade           TEXT,

    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- =============================================================================
-- FACT: fact_aum
-- One row per fund house per month (source: 03_aum_by_fund_house.csv)
-- Grain: fund_house + date
-- NOTE: fund_house is plain text, NOT a foreign key — AMFI publishes AUM at
-- the AMC level, not per individual scheme, so it can't join to dim_fund.amfi_code.
-- =============================================================================
DROP TABLE IF EXISTS fact_aum;
CREATE TABLE fact_aum (
    aum_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house        TEXT NOT NULL,
    date_id           INTEGER NOT NULL,
    aum_lakh_crore    REAL,
    aum_crore         INTEGER NOT NULL CHECK (aum_crore >= 0),
    num_schemes       INTEGER,

    FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    UNIQUE (fund_house, date_id)
);

-- =============================================================================
-- Helpful indexes for common query patterns (joins + filters)
-- =============================================================================
CREATE INDEX idx_fact_nav_amfi_date       ON fact_nav (amfi_code, date_id);
CREATE INDEX idx_fact_txn_amfi            ON fact_transactions (amfi_code);
CREATE INDEX idx_fact_txn_date            ON fact_transactions (date_id);
CREATE INDEX idx_fact_txn_state           ON fact_transactions (state);
CREATE INDEX idx_fact_aum_fundhouse_date  ON fact_aum (fund_house, date_id);
