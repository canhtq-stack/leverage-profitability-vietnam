# =============================================================================
# MMQREG_Analysis_Final.py
# Phân tích tác động của đòn bẩy tài chính đến lợi nhuận doanh nghiệp
# Phương pháp: OLS (baseline) + Quantile Regression (MMQREG proxy)
# Robustness: Bootstrap 1,000 lần + Subgroup + LEV_lag1 (xử lý reverse causality)
# =============================================================================

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.quantile_regression import QuantReg
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib.pyplot as plt
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 0. CẤU HÌNH — THAY ĐỔI Ở ĐÂY NẾU CẦN
# =============================================================================
BASE_PATH     = r"."   # Update to your local data directory if needed
OUTPUT_FOLDER = os.path.join(BASE_PATH, "outputs")
INPUT_FILE    = os.path.join(BASE_PATH, "data",
                             "10_DuLieu_MMQREG_FINAL_With_Industry.xlsx")

Y_VAR   = 'ROA'
X_VARS  = ['LEV', 'SIZE', 'TANG', 'LIQ', 'AGE']   # biến kiểm soát, không đổi
QUANTS  = [0.10, 0.25, 0.50, 0.75, 0.90]
N_BOOT  = 1_000   # số lần bootstrap
SEED    = 42

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print("=" * 70)
print("BẮT ĐẦU PHÂN TÍCH MMQREG – BẢN CUỐI")
print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# =============================================================================
# 1. ĐỌC & CHUẨN BỊ DỮ LIỆU
# =============================================================================
if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Không tìm thấy file đầu vào:\n{INPUT_FILE}")

df_raw = pd.read_excel(INPUT_FILE)
print(f"\n[1] Đọc dữ liệu: {len(df_raw):,} quan sát | "
      f"{df_raw['Ticker'].nunique()} doanh nghiệp | "
      f"{df_raw['Year'].min()}–{df_raw['Year'].max()}")

# --- Winsorize (1%, 99%) ---
def winsorize(series, lo=0.01, hi=0.01):
    lo_val, hi_val = np.percentile(series.dropna(), [lo * 100, (1 - hi) * 100])
    return series.clip(lo_val, hi_val)

df = df_raw.copy()
for col in [Y_VAR] + X_VARS:
    df[col] = winsorize(df[col])

# --- Tạo LEV_lag1 (biến trễ 1 năm của LEV) ---
df = df.sort_values(['Ticker', 'Year'])
df['LEV_lag1'] = df.groupby('Ticker')['LEV'].shift(1)

# --- Dataset chính (dùng LEV đương kỳ) ---
df_main = df[[Y_VAR] + X_VARS + ['Ticker', 'Year', 'IndustryName']].dropna().copy()

# --- Dataset robustness (dùng LEV_lag1 thay LEV) ---
x_lag = ['LEV_lag1'] + [v for v in X_VARS if v != 'LEV']
df_lag = df[[Y_VAR] + x_lag + ['Ticker', 'Year']].dropna().copy()

print(f"    Dataset chính   : {len(df_main):,} obs  "
      f"({df_main['Ticker'].nunique()} firms)")
print(f"    Dataset lag-LEV : {len(df_lag):,} obs  "
      f"({df_lag['Ticker'].nunique()} firms)  "
      f"[mất năm đầu mỗi firm do lag]")

# =============================================================================
# 2. HÀM TIỆN ÍCH
# =============================================================================
def sig_star(p):
    if p < 0.01:  return '***'
    if p < 0.05:  return '**'
    if p < 0.10:  return '*'
    return ''

def run_ols(y, X, groups):
    return sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': groups})

def run_qreg_all(y, X, quantiles):
    """Chạy QR cho nhiều quantile, trả về dict {q: model}."""
    return {q: QuantReg(y, X).fit(q=q, max_iter=1000) for q in quantiles}

def build_result_table(ols_m, qreg_dict, x_labels, quantiles, y, X):
    """Ghép OLS + QR thành DataFrame đẹp. y và X được truyền tường minh."""
    rows = []
    for var in x_labels:
        row = {'Variable': var}
        row['OLS'] = f"{ols_m.params[var]:.4f}{sig_star(ols_m.pvalues[var])}"
        for q in quantiles:
            m   = qreg_dict[q]
            lbl = f"Q{int(q*100)}"
            row[lbl] = f"{m.params[var]:.4f}{sig_star(m.pvalues[var])}"
        rows.append(row)
    # R² / Pseudo-R²
    r2_row = {'Variable': 'R² / Pseudo-R²',
              'OLS': f"{ols_m.rsquared:.4f}"}
    for q in quantiles:
        m       = qreg_dict[q]
        fitted  = m.predict(X)
        resid_m = np.abs(y - fitted)
        resid_0 = np.abs(y - y.quantile(q))
        psr2    = 1 - resid_m.sum() / resid_0.sum()
        r2_row[f"Q{int(q*100)}"] = f"{psr2:.4f}"
    rows.append(r2_row)
    return pd.DataFrame(rows)

# =============================================================================
# 3. VIF CHECK
# =============================================================================
print("\n[2] Kiểm tra VIF...")
X_vif = df_main[X_VARS]
vif_df = pd.DataFrame({
    'Variable': X_VARS,
    'VIF': [round(variance_inflation_factor(X_vif.values, i), 3)
            for i in range(len(X_VARS))]
})
print(vif_df.to_string(index=False))
vif_df.to_excel(os.path.join(OUTPUT_FOLDER, "01_VIF.xlsx"), index=False)

# =============================================================================
# 4. MÔ HÌNH CHÍNH: OLS + QR (LEV đương kỳ)
# =============================================================================
print("\n[3] Chạy mô hình chính (LEV đương kỳ)...")

y_main  = df_main[Y_VAR]
X_main  = sm.add_constant(df_main[X_VARS])
grp_main = df_main['Ticker']

ols_main  = run_ols(y_main, X_main, grp_main)
qreg_main = run_qreg_all(y_main, X_main, QUANTS)

# In nhanh hệ số LEV
print(f"  OLS  LEV: {ols_main.params['LEV']:.4f} "
      f"(p={ols_main.pvalues['LEV']:.4f}){sig_star(ols_main.pvalues['LEV'])}")
for q, m in qreg_main.items():
    print(f"  Q{int(q*100):2d}  LEV: {m.params['LEV']:.4f} "
          f"(p={m.pvalues['LEV']:.4f}){sig_star(m.pvalues['LEV'])}")

# Build & lưu bảng kết quả chính
tbl_main = build_result_table(ols_main, qreg_main,
                              list(X_main.columns), QUANTS,
                              y_main, X_main)
tbl_main.to_excel(os.path.join(OUTPUT_FOLDER, "02_Main_Results.xlsx"), index=False)
print("  → Lưu: 02_Main_Results.xlsx")

# =============================================================================
# 5. ROBUSTNESS A: BOOTSTRAP 1,000 LẦN
# =============================================================================
print(f"\n[4] Bootstrap {N_BOOT} lần (LEV đương kỳ)...")
np.random.seed(SEED)
boot_coefs = {q: [] for q in QUANTS}
n = len(df_main)

for b in range(N_BOOT):
    idx   = np.random.choice(n, n, replace=True)
    y_b   = y_main.iloc[idx].reset_index(drop=True)
    X_b   = X_main.iloc[idx].reset_index(drop=True)
    for q in QUANTS:
        m = QuantReg(y_b, X_b).fit(q=q, max_iter=1000)
        boot_coefs[q].append(m.params['LEV'])
    if (b + 1) % 200 == 0:
        print(f"  ... {b+1}/{N_BOOT} lần xong")

boot_rows = []
for q in QUANTS:
    arr  = np.array(boot_coefs[q])
    ci_lo, ci_hi = np.percentile(arr, [2.5, 97.5])
    p_val = 2 * min((arr >= 0).mean(), (arr < 0).mean())   # two-tailed
    boot_rows.append({
        'Quantile'  : f"Q{int(q*100)}",
        'Mean_Coef' : round(arr.mean(), 4),
        'Std_Boot'  : round(arr.std(), 4),
        'CI_95_Low' : round(ci_lo, 4),
        'CI_95_High': round(ci_hi, 4),
        'p_bootstrap': round(p_val, 4),
        'Sig'       : sig_star(p_val)
    })

df_boot = pd.DataFrame(boot_rows)
df_boot.to_excel(os.path.join(OUTPUT_FOLDER, "03_Bootstrap_Results.xlsx"),
                 index=False)
print("  → Lưu: 03_Bootstrap_Results.xlsx")
print(df_boot[['Quantile', 'Mean_Coef', 'CI_95_Low', 'CI_95_High',
               'p_bootstrap', 'Sig']].to_string(index=False))

# =============================================================================
# 6. ROBUSTNESS B: SUBGROUP (SIZE & LEV)
# =============================================================================
print("\n[5] Subgroup analysis (SIZE & LEV)...")
df_main['SIZE_GRP'] = pd.qcut(df_main['SIZE'], 3,
                               labels=['Small', 'Medium', 'Large'])
df_main['LEV_GRP']  = pd.qcut(df_main['LEV'],  3,
                               labels=['Low', 'Medium', 'High'])

sub_rows = []
for grp_col, grp_name in [('SIZE_GRP', 'Size'), ('LEV_GRP', 'Leverage')]:
    for g in ['Small', 'Medium', 'Large'] if grp_name == 'Size' \
             else ['Low', 'Medium', 'High']:
        sub = df_main[df_main[grp_col] == g]
        if len(sub) < 30:
            continue
        ys  = sub[Y_VAR]
        Xs  = sm.add_constant(sub[X_VARS])
        m50 = QuantReg(ys, Xs).fit(q=0.50, max_iter=1000)
        sub_rows.append({
            'Stratification': grp_name,
            'Group'         : g,
            'N_obs'         : len(sub),
            'LEV_Q50_Coef'  : round(m50.params['LEV'], 4),
            'LEV_Q50_SE'    : round(m50.bse['LEV'], 4),
            'p_value'       : round(m50.pvalues['LEV'], 4),
            'Sig'           : sig_star(m50.pvalues['LEV'])
        })

df_sub = pd.DataFrame(sub_rows)
df_sub.to_excel(os.path.join(OUTPUT_FOLDER, "04_Subgroup_Results.xlsx"),
                index=False)
print("  → Lưu: 04_Subgroup_Results.xlsx")
print(df_sub[['Stratification', 'Group', 'N_obs',
              'LEV_Q50_Coef', 'p_value', 'Sig']].to_string(index=False))

# =============================================================================
# 7. ROBUSTNESS C: LEV_lag1 — XỬ LÝ REVERSE CAUSALITY  ← MỚI
# =============================================================================
print("\n[6] Robustness: LEV_lag1 (xử lý reverse causality)...")

y_lag  = df_lag[Y_VAR]
X_lag  = sm.add_constant(df_lag[x_lag])
grp_lag = df_lag['Ticker']

ols_lag  = run_ols(y_lag, X_lag, grp_lag)
qreg_lag = run_qreg_all(y_lag, X_lag, QUANTS)

print(f"  OLS  LEV_lag1: {ols_lag.params['LEV_lag1']:.4f} "
      f"(p={ols_lag.pvalues['LEV_lag1']:.4f})"
      f"{sig_star(ols_lag.pvalues['LEV_lag1'])}")
for q, m in qreg_lag.items():
    print(f"  Q{int(q*100):2d}  LEV_lag1: {m.params['LEV_lag1']:.4f} "
          f"(p={m.pvalues['LEV_lag1']:.4f})"
          f"{sig_star(m.pvalues['LEV_lag1'])}")

# Build bảng so sánh LEV vs LEV_lag1
compare_rows = []
for q in QUANTS:
    m_cur = qreg_main[q]
    m_lag = qreg_lag[q]
    compare_rows.append({
        'Quantile'        : f"Q{int(q*100)}",
        'LEV_Coef'        : round(m_cur.params['LEV'], 4),
        'LEV_Sig'         : sig_star(m_cur.pvalues['LEV']),
        'LEV_lag1_Coef'   : round(m_lag.params['LEV_lag1'], 4),
        'LEV_lag1_Sig'    : sig_star(m_lag.pvalues['LEV_lag1']),
        'Direction_Same'  : 'Yes' if (m_cur.params['LEV'] * m_lag.params['LEV_lag1']) > 0
                            else 'No'
    })

# Thêm dòng OLS
compare_rows.insert(0, {
    'Quantile'      : 'OLS',
    'LEV_Coef'      : round(ols_main.params['LEV'], 4),
    'LEV_Sig'       : sig_star(ols_main.pvalues['LEV']),
    'LEV_lag1_Coef' : round(ols_lag.params['LEV_lag1'], 4),
    'LEV_lag1_Sig'  : sig_star(ols_lag.pvalues['LEV_lag1']),
    'Direction_Same': 'Yes' if (ols_main.params['LEV'] *
                                ols_lag.params['LEV_lag1']) > 0 else 'No'
})

df_compare = pd.DataFrame(compare_rows)
df_compare.to_excel(os.path.join(OUTPUT_FOLDER, "05_LEV_vs_LEVlag1.xlsx"),
                    index=False)
print("  → Lưu: 05_LEV_vs_LEVlag1.xlsx")
print(df_compare.to_string(index=False))

# =============================================================================
# 8. BIỂU ĐỒ
# =============================================================================
print("\n[7] Vẽ biểu đồ...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Hệ số LEV theo phân vị ROA: So sánh đương kỳ vs. Trễ 1 năm",
             fontsize=13, fontweight='bold')

qs_label = [f"Q{int(q*100)}" for q in QUANTS]

# -- Panel trái: LEV đương kỳ --
coefs_cur = [qreg_main[q].params['LEV'] for q in QUANTS]
ses_cur   = [qreg_main[q].bse['LEV']    for q in QUANTS]
axes[0].plot(qs_label, coefs_cur, marker='o', linewidth=2.5,
             color='#2166ac', label='LEV (đương kỳ)')
axes[0].fill_between(qs_label,
                     [c - 1.96*s for c, s in zip(coefs_cur, ses_cur)],
                     [c + 1.96*s for c, s in zip(coefs_cur, ses_cur)],
                     alpha=0.15, color='#2166ac')
axes[0].axhline(ols_main.params['LEV'], color='red', linestyle='--',
                linewidth=1.8,
                label=f"OLS = {ols_main.params['LEV']:.4f}")
axes[0].axhline(0, color='black', linewidth=0.8, linestyle=':')
axes[0].set_title("Mô hình chính (LEV đương kỳ)")
axes[0].set_xlabel("Phân vị ROA")
axes[0].set_ylabel("Hệ số LEV")
axes[0].legend(); axes[0].grid(alpha=0.3)

# -- Panel phải: LEV_lag1 --
coefs_lag = [qreg_lag[q].params['LEV_lag1'] for q in QUANTS]
ses_lag   = [qreg_lag[q].bse['LEV_lag1']    for q in QUANTS]
axes[1].plot(qs_label, coefs_lag, marker='s', linewidth=2.5,
             color='#d6604d', label='LEV_lag1 (trễ 1 năm)')
axes[1].fill_between(qs_label,
                     [c - 1.96*s for c, s in zip(coefs_lag, ses_lag)],
                     [c + 1.96*s for c, s in zip(coefs_lag, ses_lag)],
                     alpha=0.15, color='#d6604d')
axes[1].axhline(ols_lag.params['LEV_lag1'], color='green', linestyle='--',
                linewidth=1.8,
                label=f"OLS = {ols_lag.params['LEV_lag1']:.4f}")
axes[1].axhline(0, color='black', linewidth=0.8, linestyle=':')
axes[1].set_title("Robustness: LEV_lag1 (trễ 1 năm)")
axes[1].set_xlabel("Phân vị ROA")
axes[1].set_ylabel("Hệ số LEV_lag1")
axes[1].legend(); axes[1].grid(alpha=0.3)

plt.tight_layout()
plot_path = os.path.join(OUTPUT_FOLDER, "06_Quantile_Plots_Main_vs_Lag.png")
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  → Lưu biểu đồ: 06_Quantile_Plots_Main_vs_Lag.png")

# =============================================================================
# 9. THỐNG KÊ MÔ TẢ
# =============================================================================
print("\n[8] Thống kê mô tả...")

desc_full = df_main[[Y_VAR] + X_VARS].describe().T[
    ['count', 'mean', 'std', 'min', 'max']].round(4)
desc_full.index.name = 'Variable'
desc_full.to_excel(os.path.join(OUTPUT_FOLDER, "07_Descriptive_Stats.xlsx"))

# Theo năm
desc_year = df_main.groupby('Year')[[Y_VAR, 'LEV', 'SIZE']].mean().round(4)
desc_year.to_excel(os.path.join(OUTPUT_FOLDER, "08_Desc_by_Year.xlsx"))

# Theo ngành
desc_ind  = df_main.groupby('IndustryName')[[Y_VAR] + X_VARS].mean().round(4)
desc_ind.to_excel(os.path.join(OUTPUT_FOLDER, "09_Desc_by_Industry.xlsx"))

print("  → Lưu: 07_Descriptive_Stats.xlsx | 08_Desc_by_Year.xlsx | "
      "09_Desc_by_Industry.xlsx")

# =============================================================================
# 10. TÓM TẮT CUỐI
# =============================================================================
print("\n" + "=" * 70)
print("HOÀN TẤT – CÁC FILE ĐÃ TẠO:")
print("=" * 70)
for f in sorted(os.listdir(OUTPUT_FOLDER)):
    if f.endswith(('.xlsx', '.png')):
        fpath = os.path.join(OUTPUT_FOLDER, f)
        size  = os.path.getsize(fpath) / 1024
        print(f"  {f:<45} {size:>7.1f} KB")

print(f"\nOutput folder: {OUTPUT_FOLDER}")
print("=" * 70)

# Mở thư mục output (Windows)
try:
    os.startfile(OUTPUT_FOLDER)
except Exception:
    pass
