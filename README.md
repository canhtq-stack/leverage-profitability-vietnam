# Replication Package

## The Heterogeneous Impact of Financial Leverage on Profitability: Evidence from Vietnam Using Method of Moments Quantile Regression

**Authors:** Le Khoa Huan, Tran Quang Canh, Vu Truc Phuc  
**Journal:** Emerging Markets Finance and Trade (under review)  
**Corresponding author:** canhtq@uef.edu.vn

---

## Overview

This repository contains the replication code for all empirical results reported in the paper. The study employs Method of Moments Quantile Regression (MMQREG) alongside baseline OLS to examine the heterogeneous impact of financial leverage on firm profitability among the 50 largest non-financial firms listed on the Ho Chi Minh Stock Exchange (HOSE) over 2015–2024.

---

## Repository Structure

```
├── analysis.py            # Main analysis script (OLS + QR + all robustness checks)
├── requirements.txt       # Python package dependencies with pinned versions
├── data/
│   └── README_data.md     # Data sources and access instructions
└── outputs/               # Generated tables and figures (auto-created by script)
    ├── 01_VIF.xlsx
    ├── 02_Main_Results.xlsx
    ├── 03_Bootstrap_Results.xlsx
    ├── 04_Subgroup_Results.xlsx
    ├── 05_LEV_vs_LEVlag1.xlsx
    └── 06_Quantile_Plots_Main_vs_Lag.png
```

---

## Data

### Source
- **Primary:** TCBS Financial Data API (https://www.tcbs.com.vn)
- **Cross-verification:** Audited annual reports, publicly available via the Ho Chi Minh Stock Exchange (https://www.hsx.vn)

### Variables
| Variable | Definition |
|---|---|
| ROA | Net income after tax / Total assets |
| LEV | Total debt / Total assets |
| SIZE | Natural logarithm of total assets |
| TANG | Fixed assets / Total assets |
| LIQ | Cash and cash equivalents / Total assets |
| AGE | Years since listing on HOSE |

### Sample
- 50 largest non-financial firms listed on HOSE
- Period: 2015–2024
- Final unbalanced panel: 496 firm-year observations (4 excluded due to incomplete disclosures)
- Outliers addressed via Winsorisation at 1st and 99th percentiles

> **Note on data availability:** The raw dataset is available from the corresponding author upon reasonable request at canhtq@uef.edu.vn. Due to TCBS API terms of service, the full dataset cannot be publicly redistributed. Reviewers requiring data access for replication purposes may contact the corresponding author directly.

---

## Replication Instructions

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure paths
Open `analysis.py` and update **Section 0 — Configuration** (lines 20–25):

```python
BASE_PATH     = r"path/to/your/data/folder"
OUTPUT_FOLDER = os.path.join(BASE_PATH, "outputs")
INPUT_FILE    = os.path.join(BASE_PATH, "data",
                             "10_DuLieu_MMQREG_FINAL_With_Industry.xlsx")
```

### 3. Run the analysis
```bash
python analysis.py
```

### 4. Expected outputs
The script produces 9 output files in the `outputs/` folder:

| File | Content | Corresponds to |
|---|---|---|
| `01_VIF.xlsx` | Variance Inflation Factors | Section 3.3 |
| `02_Main_Results.xlsx` | OLS + QR coefficients | Tables 5 & 6 |
| `03_Bootstrap_Results.xlsx` | Bootstrap CI (1,000 replications) | Table 7 (bootstrap panel) |
| `04_Subgroup_Results.xlsx` | Size & leverage subgroups | Table 7 (subgroup panel) |
| `05_LEV_vs_LEVlag1.xlsx` | Contemporaneous vs. lagged LEV | Table 8 |
| `06_Quantile_Plots_Main_vs_Lag.png` | Coefficient plot | Figure in paper |
| `07_Descriptive_Stats.xlsx` | Full sample descriptives | Table 1 |
| `08_Desc_by_Year.xlsx` | Annual trends | Table 4 |
| `09_Desc_by_Industry.xlsx` | Industry breakdown | Table 3 |

---

## Reproducibility

- All random seeds are fixed: `SEED = 42` (set in analysis.py, Section 0)
- Bootstrap replications: `N_BOOT = 1000`
- Python version used: 3.11.x
- Results are fully reproducible with the pinned package versions in `requirements.txt`

---

## Key Methods

| Method | Purpose | Reference |
|---|---|---|
| OLS with clustered SE | Baseline average effect | Cameron & Miller (2015) |
| Quantile Regression (MMQREG) | Distributional heterogeneity | Machado & Santos Silva (2019) |
| Bootstrap (1,000 reps) | Inferential robustness | — |
| Lagged LEV specification | Reverse causality check | — |
| Subgroup analysis | Heterogeneity by size/leverage | — |

---

## Citation

If you use this code, please cite:

> Le, K. H., Tran, Q. C., & Vu, T. P. (under review). The Heterogeneous Impact of Financial Leverage on Profitability: Evidence from Vietnam Using Method of Moments Quantile Regression. *Emerging Markets Finance and Trade*.

---

## License

This code is shared for academic replication purposes only.
