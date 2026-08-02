# Data Dictionary - MF Analytics Platform

I built this document to explain every table and column in my SQLite database (`bluestock_mf.db`), so anyone reviewing my project can understand what each field means and where it came from.

## Tables I Built

| Table | Rows | What it holds |
|---|---|---|
| `dim_fund` | 40 | One row per mutual fund scheme |
| `dim_date` | 1,826 | One row per calendar date (2022–2026) |
| `fact_nav` | 64,320 | Daily NAV for every scheme |
| `fact_transactions` | 32,778 | Every investor transaction |
| `fact_performance` | 40 | Return and risk metrics per scheme |
| `fact_aum` | 90 | AUM per fund house per quarter |
| `fact_sip` | 48 | Industry-wide monthly SIP stats |

---

## dim_fund
Source: `01_fund_master.csv` | Primary Key: `amfi_code`

| Column | Type | What it means |
|---|---|---|
| `amfi_code` | INTEGER | Unique ID for each scheme, assigned by AMFI. I use this to link every other table back to this one. |
| `fund_house` | TEXT | The AMC that runs the fund, e.g. SBI Mutual Fund. |
| `scheme_name` | TEXT | Full scheme name, including plan type. |
| `category` | TEXT | Equity or Debt. |
| `sub_category` | TEXT | Large Cap, Small Cap, Gilt, Liquid, etc. |
| `plan` | TEXT | Regular or Direct. |
| `launch_date` | DATE | When the scheme launched. |
| `benchmark` | TEXT | The index this fund is compared against. |
| `expense_ratio_pct` | REAL | Annual fee, as a % of AUM. |
| `exit_load_pct` | REAL | Penalty fee for early redemption. |
| `min_sip_amount` | INTEGER | Minimum monthly SIP amount (₹). |
| `min_lumpsum_amount` | INTEGER | Minimum lumpsum investment (₹). |
| `fund_manager` | TEXT | Who manages the fund. |
| `risk_category` | TEXT | Low to Very High risk grade. |
| `sebi_category_code` | TEXT | SEBI's classification code - shared across many schemes, not unique. |

---

## dim_date
Source: I generated this myself with `pd.date_range()` | Primary Key: `date_id`

| Column | Type | What it means |
|---|---|---|
| `date_id` | INTEGER | Date written as a number, like `20220103`. I use this to join dates faster. |
| `full_date` | DATE | The actual date. |
| `year` / `quarter` / `month` / `day` | INTEGER | Standard date parts. |
| `month_name` / `day_name` | TEXT | e.g. "January", "Monday". |
| `is_weekend` | INTEGER | 1 if Saturday/Sunday. |
| `is_month_end` | INTEGER | 1 if it's the last day of the month. |

---

## fact_nav
Source: `02_nav_history_cleaned.csv` | Links to `dim_fund` and `dim_date`

| Column | Type | What it means |
|---|---|---|
| `nav_id` | INTEGER | Row ID, auto-generated. |
| `amfi_code` | INTEGER | Which scheme this NAV is for. |
| `date_id` | INTEGER | Which day this NAV is for. |
| `nav` | REAL | The fund's per-unit price that day, in ₹. I forward-filled weekends/holidays during cleaning so every day has a value. |

---

## fact_transactions
Source: `08_investor_transactions_cleaned.csv` | Links to `dim_fund` and `dim_date`

| Column | Type | What it means |
|---|---|---|
| `transaction_id` | INTEGER | Row ID, auto-generated. |
| `investor_id` | TEXT | Who made the transaction. |
| `amfi_code` | INTEGER | Which scheme it's for. |
| `date_id` | INTEGER | When it happened. |
| `transaction_type` | TEXT | SIP, Lumpsum, or Redemption - I standardized these during cleaning. |
| `amount_inr` | INTEGER | Transaction amount (₹). |
| `state` / `city` / `city_tier` | TEXT | Investor's location. T30 = top 30 cities, B30 = smaller cities. |
| `age_group` / `gender` | TEXT | Investor demographics. |
| `annual_income_lakh` | REAL | Investor's reported income (₹ lakh). |
| `payment_mode` | TEXT | How they paid - UPI, Cheque, Mandate, etc. |
| `kyc_status` | TEXT | Verified or Pending. |

---

## fact_performance
Source: `07_scheme_performance_cleaned.csv` | Links to `dim_fund` | One snapshot per scheme, no date

| Column | Type | What it means |
|---|---|---|
| `amfi_code` | INTEGER | Which scheme this is for. |
| `return_1yr_pct` / `return_3yr_pct` / `return_5yr_pct` | REAL | Returns over 1, 3, 5 years. |
| `benchmark_3yr_pct` | REAL | How the benchmark performed over 3 years, for comparison. |
| `alpha` | REAL | How much the fund beat its benchmark, risk-adjusted. |
| `beta` | REAL | How volatile the fund is vs the market. |
| `sharpe_ratio` | REAL | Return per unit of risk. I noticed Liquid funds show very high values here since their volatility is near zero - that's expected, not an error. |
| `sortino_ratio` | REAL | Like Sharpe, but only counts downside risk. |
| `std_dev_ann_pct` | REAL | How much the fund's returns swing around. |
| `max_drawdown_pct` | REAL | The worst peak-to-trough loss. Always negative or zero. |
| `aum_crore` | INTEGER | AUM for this specific scheme (₹ crore). |
| `expense_ratio_pct` | REAL | Annual fee %. |
| `morningstar_rating` | INTEGER | Star rating, 1 to 5. |
| `risk_grade` | TEXT | Risk level for this scheme. |

---

## fact_aum
Source: `03_aum_by_fund_house.csv` | Links to `dim_date` only

| Column | Type | What it means |
|---|---|---|
| `aum_id` | INTEGER | Row ID, auto-generated. |
| `fund_house` | TEXT | The AMC. I couldn't link this to `dim_fund` since AMFI reports AUM per fund house, not per scheme. |
| `date_id` | INTEGER | The reporting date. |
| `aum_lakh_crore` / `aum_crore` | REAL / INTEGER | Total AUM, in two different units. |
| `num_schemes` | INTEGER | How many schemes the AMC had active. |

---

## fact_sip
Source: `04_monthly_sip_inflows_cleaned.csv` | Standalone - no foreign keys

I added this table later, since I needed it for my SIP YoY growth query and it wasn't part of my original 6-table plan.

| Column | Type | What it means |
|---|---|---|
| `month` | TEXT | Month in `YYYY-MM` format. |
| `sip_inflow_crore` | INTEGER | Total industry SIP inflow that month (₹ crore). |
| `active_sip_accounts_crore` | REAL | Active SIP accounts industry-wide (crore). |
| `new_sip_accounts_lakh` | REAL | New SIP accounts added that month (lakh). |
| `sip_aum_lakh_crore` | REAL | AUM coming from SIPs. |
| `yoy_growth_pct` | REAL | Growth vs the same month last year. I left this blank for the first 12 months since there's no prior year to compare against. |

---
