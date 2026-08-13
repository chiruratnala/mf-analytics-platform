-- =============================================================================
-- MF Analytics Platform — 10 Analytical SQL Queries
-- Bluestock Fintech Capstone · Day 2
-- Database: bluestock_mf.db
-- =============================================================================


-- =============================================================================
-- Query 1: Top 5 funds by AUM
-- =============================================================================
SELECT f.scheme_name, f.fund_house, p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;


-- =============================================================================
-- Query 2: Average NAV per month
-- =============================================================================
SELECT d.year, d.month, d.month_name, ROUND(AVG(n.nav), 2) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- =============================================================================
-- Query 3: SIP YoY growth
-- =============================================================================
SELECT month, sip_inflow_crore, active_sip_accounts_crore, yoy_growth_pct
FROM fact_sip
ORDER BY month;


-- =============================================================================
-- Query 4: Transactions by state
-- =============================================================================
SELECT
    state,
    COUNT(*) AS total_transactions,
    SUM(amount_inr) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_transaction_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- =============================================================================
-- Query 5: Funds with expense_ratio < 1%
-- =============================================================================
SELECT f.scheme_name, f.fund_house, p.expense_ratio_pct, f.category
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio_pct < 1.0
ORDER BY p.expense_ratio_pct ASC;


-- =============================================================================
-- Query 6: Top 5 fund houses by total AUM (latest snapshot)
-- =============================================================================
SELECT
    fund_house,
    aum_crore,
    num_schemes
FROM fact_aum
WHERE date_id = (SELECT MAX(date_id) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5;


-- =============================================================================
-- Query 7: SIP vs Lumpsum vs Redemption — transaction volume and value breakdown
-- =============================================================================
SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_value_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_transactions), 2) AS pct_of_transactions
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_value_inr DESC;


-- =============================================================================
-- Query 8: Best risk-adjusted performers — top 5 by Sharpe ratio (excluding Liquid funds)
-- =============================================================================
SELECT
    f.scheme_name,
    f.fund_house,
    f.category,
    f.sub_category,
    p.sharpe_ratio,
    p.sortino_ratio,
    p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE f.sub_category != 'Liquid'
ORDER BY p.sharpe_ratio DESC
LIMIT 5;


-- =============================================================================
-- Query 9: Investor demographics — transaction value by age group and gender
-- =============================================================================
SELECT
    age_group,
    gender,
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_value_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY age_group, gender
ORDER BY age_group, gender;


-- =============================================================================
-- Query 10: KYC status breakdown — Verified vs Pending, and value at risk
-- =============================================================================
SELECT
    kyc_status,
    COUNT(*) AS transaction_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_transactions), 2) AS pct_of_transactions,
    SUM(amount_inr) AS total_value_inr,
    ROUND(SUM(amount_inr) * 100.0 / (SELECT SUM(amount_inr) FROM fact_transactions), 2) AS pct_of_total_value
FROM fact_transactions
GROUP BY kyc_status
ORDER BY total_value_inr DESC;
