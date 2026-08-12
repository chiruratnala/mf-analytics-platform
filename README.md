# Bluestock Fintech --- Mutual Fund Analytics Platform

An end-to-end **Mutual Fund Analytics Platform** developed as an
individual capstone project for **Bluestock Fintech**. The project
consolidates mutual fund data, applies an ETL pipeline, stores
structured data in a relational database, performs exploratory and
financial analysis, and presents insights through an interactive Power
BI dashboard.

> **Project Type:** Individual Capstone Project\
> **Domain:** Mutual Fund Analytics / Financial Data Analytics\
> **Primary Tools:** Python, SQL, Power BI, Pandas, NumPy, Matplotlib,
> Seaborn

------------------------------------------------------------------------

## 1. Project Overview

The Indian mutual fund ecosystem contains large volumes of NAV, AUM,
SIP, investor and market benchmark data. These datasets are available in
different formats and require transformation before meaningful analysis
can be performed.

This project builds a unified analytics workflow to:

-   Track NAV movements across **40 selected mutual fund schemes**
-   Analyse AUM growth across major fund houses
-   Study SIP inflow and investor transaction patterns
-   Analyse investor demographics and geographic behaviour
-   Calculate fund performance and risk metrics
-   Compare mutual fund performance with benchmark indices
-   Analyse portfolio/sector allocation
-   Provide an interactive dashboard for fund comparison and decision
    support

The overall workflow is:

``` text
Raw Data
   ↓
Data Extraction
   ↓
Data Cleaning & Transformation
   ↓
ETL Pipeline
   ↓
Relational Database
   ↓
EDA + Financial Metrics
   ↓
Power BI Dashboard
   ↓
Business Insights & Recommendations
```

------------------------------------------------------------------------

## 2. Business Problems Addressed

### P1 --- Data Fragmentation

NAV, AUM, SIP and investor-related information are available across
different datasets and formats.

**Solution:** Build an ETL workflow that cleans and consolidates the
required datasets into a structured analytical database.

### P2 --- Performance Comparison Gap

Investors need a consistent way to compare funds using returns as well
as risk-adjusted measures.

**Solution:** Calculate return, volatility and risk-adjusted performance
metrics and present them together.

### P3 --- Benchmark Tracking

Fund performance is more meaningful when compared with relevant market
benchmarks.

**Solution:** Compare selected schemes against benchmark indices such as
Nifty 50 and Nifty 100 where applicable.

### P4 --- Investor Behaviour Blind Spot

Investor activity can vary by age, gender, geography and city tier.

**Solution:** Analyse transaction and SIP patterns across demographic
and geographic segments.

### P5 --- Slow / Static Reporting

Static reports make it difficult to filter funds and investigate trends
interactively.

**Solution:** Build an interactive Power BI dashboard with filters,
drill-down analysis and multiple analytical views.

------------------------------------------------------------------------

## 3. Key Project Objectives

  -----------------------------------------------------------------------
  ID                      Objective               Outcome
  ----------------------- ----------------------- -----------------------
  O1                      Build an ETL pipeline   Automated Python
                                                  pipeline

  O2                      Design structured       Relational analytical
                          database storage        schema

  O3                      Perform EDA on NAV and  Analytical charts and
                          AUM data                insights

  O4                      Calculate performance   Fund performance
                          and risk metrics        analysis

  O5                      Build an interactive BI Power BI dashboard
                          dashboard               

  O6                      Analyse investor        Demographic and
                          behaviour               geographic insights

  O7                      Compare funds with      Benchmark/performance
                          benchmarks              analysis

  O8                      Document the project    README, report and
                                                  presentation
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Repository Structure

```text
bluestock_mf_capstone/
├── data/
│   ├── raw/           ← original downloaded files
│   ├── processed/     ← cleaned, merged CSVs
│   └── db/            ← bluestock_mf.db (SQLite)
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/
│   ├── etl_pipeline.py
│   ├── live_nav_fetch.py
│   ├── compute_metrics.py
│   └── recommender.py
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── dashboard/
│   └── bluestock_mf.pbix
├── reports/
│   ├── Final_Report.pdf
│   └── Presentation.pptx
└── README.md
```

## 5. Data Sources & Dataset Descriptions

The project uses publicly available mutual-fund and market datasets
aligned with the project requirements.

### 5.1 NAV Dataset

Contains historical Net Asset Value information for selected mutual fund
schemes.

Typical analytical fields include:

-   Date
-   Scheme name
-   Fund house / AMC
-   NAV
-   Plan
-   Growth / dividend variant where applicable

**Purpose:**

-   NAV trend analysis
-   Daily return calculation
-   1-year and 3-year return analysis
-   Volatility analysis
-   Correlation analysis
-   Sharpe ratio and other performance metrics

------------------------------------------------------------------------

### 5.2 AUM Dataset

Contains Assets Under Management information for major fund houses.

The analysis covers year-end AUM trends across the selected fund houses.

**Purpose:**

-   Fund-house comparison
-   AUM growth analysis
-   Market concentration analysis
-   Identification of leading AMCs

The analysis shows a strong increase in aggregate AUM over the period
covered by the project.

------------------------------------------------------------------------

### 5.3 SIP Inflow Dataset

Contains monthly Systematic Investment Plan inflow information.

**Purpose:**

-   Monthly SIP trend analysis
-   SIP growth analysis
-   Category-level inflow comparison
-   Identification of high-inflow fund categories

The analysis includes monthly SIP inflows from **January 2022 to
December 2025**.

------------------------------------------------------------------------

### 5.4 Investor Transaction Dataset

Contains investor-level or aggregated transaction information used for
behavioural analysis.

Relevant dimensions include:

-   State
-   Age group
-   Gender
-   City tier
-   Transaction type
-   SIP amount

**Purpose:**

-   Investor segmentation
-   State-wise transaction analysis
-   Age-wise SIP analysis
-   Gender distribution
-   T30 vs B30 comparison

------------------------------------------------------------------------

### 5.5 Benchmark Dataset

Market benchmark price/index data is used to compare mutual fund
performance.

The project includes benchmark analysis involving:

-   Nifty 50
-   Nifty 100
-   BSE SmallCap / relevant benchmark data where applicable

**Purpose:**

-   Benchmark comparison
-   Relative performance analysis
-   Alpha analysis
-   Tracking and market-performance evaluation

------------------------------------------------------------------------

### 5.6 Portfolio / Sector Allocation Dataset

Portfolio information is used to understand the aggregate sector
exposure of selected equity-oriented funds.

The analysis includes sectors such as:

-   Banking
-   IT
-   Pharma
-   Automobile
-   Utilities
-   FMCG
-   Infrastructure
-   Diversified
-   Telecom
-   Consumer Goods
-   NBFC
-   Energy
-   Cement
-   Paints

**Purpose:**

-   Sector concentration analysis
-   Portfolio diversification analysis
-   Identification of dominant sectors

------------------------------------------------------------------------

## 6. Technology Stack

### Programming & Data Analysis

-   Python
-   Pandas
-   NumPy
-   Matplotlib
-   Seaborn

### Database

-   SQL
-   SQLite / PostgreSQL, depending on the configured project environment

### Business Intelligence

-   Microsoft Power BI

### Development

-   Jupyter Notebook
-   VS Code / PyCharm
-   Git & GitHub

------------------------------------------------------------------------

## 7. Installation & Setup

### Step 1 --- Clone the Repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Bluestock-Mutual-Fund-Analytics
```

### Step 2 --- Create a Virtual Environment

Windows:

``` bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 --- Install Dependencies

``` bash
pip install -r requirements.txt
```

If `requirements.txt` is not present, install the project's required
Python packages before running the pipeline.

### Step 4 --- Configure Data / Database Settings

Place the required input datasets in the project's expected `data/raw/`
directory.

If the project uses environment variables or a configuration file for
the database, configure those values before execution.

Example:

``` text
DATABASE_URL=<your_database_connection>
```

Do not commit passwords, API keys or other secrets to GitHub.

------------------------------------------------------------------------

## 8. Running the ETL Pipeline

The project uses `run_pipeline.py` as the **master execution script**.

Run:

``` bash
python run_pipeline.py
```

The master pipeline is intended to coordinate the major ETL stages:

``` text
Extract
  ↓
Validate
  ↓
Clean
  ↓
Transform
  ↓
Load
```

### ETL Responsibilities

The pipeline prepares the raw datasets for analysis by performing tasks
such as:

-   Reading source files
-   Standardising column names
-   Converting dates into consistent formats
-   Handling missing values
-   Removing or managing duplicates
-   Cleaning categorical values
-   Converting numerical fields
-   Preparing analytical tables
-   Loading transformed data into the database

After a successful run, the processed data can be used by the analysis
notebooks and Power BI dashboard.

------------------------------------------------------------------------

## 9. Exploratory Data Analysis

The project includes EDA across several analytical dimensions.

### NAV Analysis

The analysis includes:

-   NAV trends across selected schemes
-   Indexed NAV comparison
-   Daily return correlation
-   1-year return ranking
-   3-year growth comparison
-   Market-period observations

The NAV analysis covers **40 selected schemes** across the project
period.

### AUM Analysis

Key views include:

-   Industry AUM trend
-   Year-end AUM by fund house
-   Latest AUM by AMC
-   Fund-house growth comparison

### SIP Analysis

Key views include:

-   Monthly SIP inflow trend
-   SIP inflow vs Nifty 50
-   Category-wise net inflow
-   Monthly category heatmap
-   SIP distribution by age group

### Investor Analysis

Key views include:

-   Investor distribution by age
-   Gender distribution
-   State-wise transaction/SIP amounts
-   Age group vs average SIP
-   T30 vs B30 distribution
-   Monthly transaction volume

------------------------------------------------------------------------

## 10. Performance & Risk Metrics

The project analyses mutual funds using multiple performance and risk
measures.

### Return Metrics

-   1-Year Return
-   3-Year Return
-   Indexed growth
-   Benchmark-relative performance

### Risk Metrics

-   Volatility
-   Sharpe Ratio
-   Sortino Ratio
-   Beta
-   Alpha

### Additional Analysis

-   Rolling 90-day Sharpe ratio
-   NAV return correlation
-   Benchmark comparison
-   Sector allocation
-   Risk-grade distribution

These metrics are intended to help compare funds beyond absolute return
alone.

------------------------------------------------------------------------

## 11. Selected Analytical Findings

Some notable observations from the analysis include:

### Top 1-Year Performing Schemes

The highest 1-year returns among the analysed schemes include:

    Rank Scheme                                                1-Year Return
  ------ --------------------------------------------------- ---------------
       1 ABSL Small Cap Fund - Regular - Growth                       24.93%
       2 SBI Small Cap Fund - Regular Plan - Growth                   24.56%
       3 Axis Small Cap Fund - Regular - Growth                       21.97%
       4 Nippon India Small Cap Fund - Regular - Growth               21.30%
       5 SBI Small Cap Fund - Direct Plan - Growth                    20.59%
       6 DSP Small Cap Fund - Regular - Growth                        20.20%
       7 HDFC Mid-Cap Opportunities Fund - Direct - Growth            19.98%
       8 UTI Flexi Cap Fund - Regular - Growth                        17.43%
       9 Kotak Emerging Equity Fund - Regular - Growth                17.12%
      10 ICICI Pru Value Discovery Fund - Regular - Growth            16.67%

> Past performance should not be interpreted as a guarantee of future
> returns. The rankings are based on the analysed project dataset and
> period.

### Investor Demographics

The analysed investor distribution shows:

-   **26--35:** 41.1%
-   **36--45:** 24.9%
-   **18--25:** 15.0%
-   **46--55:** 11.5%
-   **56+:** 7.5%

The 26--35 age group represents the largest segment in the analysed
dataset.

Gender distribution in the analysed dataset:

-   Male: 66.5%
-   Female: 33.5%

### SIP Trends

Monthly SIP inflows show a strong upward trend over the analysed
2022--2025 period, reaching approximately **₹31,002 crore in December
2025** in the project data.

### Fund-House AUM

The analysis shows continued AUM growth across the major fund houses
covered by the project, with SBI Mutual Fund representing the largest
AUM among the selected fund houses in the latest year shown.

------------------------------------------------------------------------

## 12. Power BI Dashboard

The project includes an interactive Power BI dashboard with multiple
analytical pages.

### Industry Overview

Includes:

-   Total AUM
-   Latest SIP inflow
-   Total schemes
-   Investor folios
-   Industry AUM trend
-   AUM by AMC

### Fund Performance

Includes:

-   Fund risk vs return
-   NAV vs benchmark
-   3-year return analysis
-   Expense ratio
-   Fund-house filters
-   Plan filters
-   Category filters
-   Scheme-level table

### Investor Analytics

Includes:

-   Transaction amount by state
-   Age group vs average SIP
-   Monthly transaction volume
-   Transaction type distribution
-   State, age group and city-tier filters

### SIP & Market Trends

Includes:

-   SIP inflow trend
-   Nifty 50 comparison
-   Top categories by net inflow
-   Monthly category-level analysis

------------------------------------------------------------------------

## 13. How to Open the Dashboard

The dashboard is developed in **Microsoft Power BI**.

### Requirements

Install:

**Power BI Desktop**

Then:

1.  Open Power BI Desktop.
2.  Select **Open**.
3.  Navigate to the dashboard folder.
4.  Open the project's `.pbix` file.
5.  If required, update the data-source/database connection.
6.  Click **Refresh** to load the latest processed data.
7.  Use the slicers and navigation buttons to explore the dashboard.

Recommended dashboard navigation:

``` text
Industry Overview
       ↓
Fund Performance
       ↓
Investor Analytics
       ↓
SIP & Market Trends
```

------------------------------------------------------------------------

## 14. Dashboard Filters

The dashboard provides interactive filtering for dimensions such as:

### Fund Performance

-   Fund House
-   Plan
-   Category
-   Scheme

### Investor Analytics

-   State
-   Age Group
-   City Tier

These filters allow users to move from a high-level industry view to
specific fund or investor segments.

------------------------------------------------------------------------

## 15. Business Recommendations

Based on the analysis, the platform can support the following business
actions:

### 1. Build a Risk-Return Fund Shortlisting View

Provide users with a fund screener combining:

-   Return
-   Volatility
-   Sharpe ratio
-   Alpha
-   Beta
-   Risk grade

This avoids selecting funds based only on historical return.

### 2. Highlight Consistent Performers

Funds that combine strong returns with favourable risk-adjusted metrics
should receive greater attention than funds that only rank highly on
one-year return.

### 3. Strengthen Small-Cap Monitoring

Several of the top 1-year performing schemes in the analysed dataset are
Small Cap funds. These should be monitored together with volatility,
drawdown and risk-adjusted measures rather than return alone.

### 4. Segment Investor Engagement

The 26--35 age group is the largest investor segment in the analysed
data. Product communication and educational content can therefore be
tailored to younger and early-career investors.

### 5. Improve Geographic Targeting

State-wise SIP and transaction analysis can identify high-activity
markets and help prioritise distribution, campaigns and investor
education.

### 6. Monitor Category-Level SIP Flows

Monthly category inflows can be tracked to identify changes in investor
preferences and emerging demand patterns.

### 7. Use Benchmark-Relative Evaluation

Fund selection should consider whether a scheme consistently adds value
relative to its appropriate benchmark instead of relying solely on
absolute returns.

### 8. Monitor Concentration Risk

The sector allocation analysis can be used to identify portfolios with
high exposure to dominant sectors such as Banking, IT and Pharma.

------------------------------------------------------------------------

## 16. Important Interpretation Notes

-   The analysis is based on the datasets and time periods included in
    this project.
-   Historical returns do not guarantee future performance.
-   Risk metrics can vary depending on the observation period and
    methodology.
-   Benchmark comparisons should use an appropriate benchmark for the
    fund category.
-   Investor transaction data should be interpreted as an analytical
    dataset and not as a complete representation of the entire Indian
    mutual fund investor population.
-   Dashboard figures may change when the underlying datasets are
    refreshed.

------------------------------------------------------------------------

## 17. Reproducibility

To reproduce the analysis:

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Bluestock-Mutual-Fund-Analytics

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

python run_pipeline.py
```

After the ETL completes:

1.  Verify the processed datasets/database.
2.  Open the Power BI `.pbix` dashboard.
3.  Refresh the data source.
4.  Review the EDA notebooks for detailed analysis.
5.  Reproduce the charts and metrics using the project
    scripts/notebooks.

------------------------------------------------------------------------

## 18. Project Deliverables

The project produces the following major deliverables:

-   Automated Python ETL pipeline
-   `run_pipeline.py` master execution script
-   Structured mutual fund analytical database
-   EDA notebooks
-   Performance and risk metrics
-   Benchmark comparison analysis
-   Investor behaviour analysis
-   Power BI interactive dashboard
-   Analytical charts and visualisations
-   Project report
-   Presentation

------------------------------------------------------------------------

## 19. Author

**Chiru Ratnala**

**Individual Capstone Project --- Mutual Fund Analytics Platform**

Developed for the **Bluestock Fintech Mutual Fund Analytics Capstone**.

------------------------------------------------------------------------

## 20. Disclaimer

This project is developed for **data analytics and educational
purposes**. The analysis and dashboard are intended to demonstrate data
engineering, financial analytics and business intelligence capabilities.

The project does **not** constitute investment advice, financial advice
or a recommendation to buy or sell any mutual fund or security.

------------------------------------------------------------------------

## License

This project is intended for educational and portfolio purposes. Add an
appropriate open-source license if the repository is intended for public
redistribution.
