# Data Access Instructions

## Input Data File

**Filename:** `10_DuLieu_MMQREG_FINAL_With_Industry.xlsx`

## Required Columns

The input Excel file must contain the following columns:

| Column | Type | Description |
|---|---|---|
| `Ticker` | string | Firm identifier (e.g., "VNM", "VHM") |
| `Year` | integer | Fiscal year (2015–2024) |
| `ROA` | float | Return on Assets = Net income / Total assets |
| `LEV` | float | Financial leverage = Total debt / Total assets |
| `SIZE` | float | Firm size = ln(Total assets) |
| `TANG` | float | Asset tangibility = Fixed assets / Total assets |
| `LIQ` | float | Liquidity = Cash / Total assets |
| `AGE` | float | Firm age = Years since HOSE listing |
| `IndustryName` | string | Industry classification (e.g., "Real Estate", "Technology") |

## Data Sources

- **TCBS Financial Data API:** https://www.tcbs.com.vn  
  *(Financial statement data: income statement, balance sheet)*
- **HOSE Disclosure Portal:** https://www.hsx.vn  
  *(Cross-verification against audited annual reports)*

## Data Availability

The raw dataset is **available from the corresponding author** upon reasonable request:

**Tran Quang Canh**  
Email: canhtq@uef.edu.vn  
Ho Chi Minh City University of Economics and Finance (UEF)

> Reviewers requiring data access for manuscript evaluation may contact the corresponding author directly. Data will be provided within 5 business days of request.

## Sample Characteristics

- **Universe:** 50 largest non-financial firms by market capitalisation on HOSE
- **Period:** 2015–2024 (10 years)
- **Final sample:** 496 firm-year observations (unbalanced panel)
- **Exclusions:** 4 observations removed due to incomplete financial disclosures
- **Outlier treatment:** Winsorisation at 1st and 99th percentiles applied to all continuous variables
