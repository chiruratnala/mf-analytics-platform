-- =============================================================================
-- MF Analytics Platform -- SQLite Star Schema
-- Bluestock Fintech Capstone - Day 2
-- Extracted directly from bluestock_mf.db via sqlite_master
-- =============================================================================

PRAGMA foreign_keys = ON;

CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date DATE,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL,
    is_month_end INTEGER NOT NULL
);

CREATE TABLE fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    nav REAL NOT NULL CHECK (nav > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    UNIQUE (amfi_code, date_id)
);

CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr INTEGER NOT NULL CHECK (amount_inr > 0),
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL CHECK (max_drawdown_pct <= 0),
    aum_crore INTEGER,
    expense_ratio_pct REAL CHECK (expense_ratio_pct BETWEEN 0.1 AND 2.5),
    morningstar_rating INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house TEXT NOT NULL,
    date_id INTEGER NOT NULL,
    aum_lakh_crore REAL,
    aum_crore INTEGER NOT NULL CHECK (aum_crore >= 0),
    num_schemes INTEGER,
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    UNIQUE (fund_house, date_id)
);

