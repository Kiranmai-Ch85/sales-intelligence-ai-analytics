"""
Step 1: Data Cleaning & Preprocessing
======================================
Smart Sales Intelligence Dashboard
Author: Manya Kumar

What this script does:
- Loads raw sales data
- Audits data quality (nulls, duplicates, dtypes)
- Fixes data types
- Engineers new features for analysis
- Saves cleaned data for EDA and SQL loading
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH    = os.path.join(BASE_DIR, 'data', 'raw_sales_data.csv')
CLEAN_PATH  = os.path.join(BASE_DIR, 'data', 'cleaned_sales_data.csv')
REPORT_PATH = os.path.join(BASE_DIR, 'outputs', 'reports', 'data_quality_report.txt')

# ── 1. LOAD ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("  SMART SALES DASHBOARD — DATA CLEANING")
print("=" * 60)

df = pd.read_csv(RAW_PATH)
print(f"\n[LOAD] Raw dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ── 2. DATA QUALITY AUDIT ─────────────────────────────────────────────────────
print("\n[AUDIT] Running data quality checks...")

report_lines = []
report_lines.append("=" * 60)
report_lines.append("  DATA QUALITY REPORT — Smart Sales Dashboard")
report_lines.append("=" * 60)
report_lines.append(f"\nDataset shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n")

# Null check
nulls = df.isnull().sum()
report_lines.append("── NULL VALUES ──────────────────────────────")
if nulls.sum() == 0:
    report_lines.append("  No null values found. ✓")
    print("  ✓ No null values found")
else:
    for col, cnt in nulls[nulls > 0].items():
        report_lines.append(f"  {col}: {cnt} nulls ({cnt/len(df)*100:.1f}%)")
        print(f"  ✗ {col}: {cnt} nulls")

# Duplicate check
dupes = df.duplicated().sum()
report_lines.append(f"\n── DUPLICATES ───────────────────────────────")
report_lines.append(f"  Duplicate rows: {dupes}")
print(f"  ✓ Duplicate rows: {dupes}")
if dupes > 0:
    df = df.drop_duplicates()
    print(f"  → Removed {dupes} duplicates")

# Data types
report_lines.append(f"\n── DATA TYPES (before fix) ──────────────────")
for col, dtype in df.dtypes.items():
    report_lines.append(f"  {col:<20} {str(dtype)}")

# Negative profit check
neg_profit = (df['profit'] < -5000).sum()
report_lines.append(f"\n── ANOMALIES ────────────────────────────────")
report_lines.append(f"  Orders with profit < -5000: {neg_profit}")
print(f"  ✓ Deep loss orders (profit < -5000): {neg_profit}")

# ── 3. FIX DATA TYPES ────────────────────────────────────────────────────────
print("\n[FIX] Converting data types...")

df['order_date'] = pd.to_datetime(df['order_date'])
df['ship_date']  = pd.to_datetime(df['ship_date'])

# ── 4. FEATURE ENGINEERING ───────────────────────────────────────────────────
print("[ENGINEER] Creating new features...")

# Date features
df['order_year']    = df['order_date'].dt.year
df['order_month']   = df['order_date'].dt.month
df['order_quarter'] = df['order_date'].dt.quarter
df['order_month_name'] = df['order_date'].dt.strftime('%b')
df['order_year_month']  = df['order_date'].dt.to_period('M').astype(str)

# Shipping speed
df['days_to_ship'] = (df['ship_date'] - df['order_date']).dt.days

# Discount bands
df['discount_band'] = pd.cut(
    df['discount'],
    bins=[-0.01, 0.0, 0.10, 0.20, 0.30, 1.0],
    labels=['No Discount', 'Low (1-10%)', 'Medium (11-20%)',
            'High (21-30%)', 'Very High (>30%)']
)

# Sales bands
df['sales_band'] = pd.cut(
    df['sales'],
    bins=[0, 2000, 10000, 30000, 100000, float('inf')],
    labels=['< ₹2K', '₹2K–10K', '₹10K–30K', '₹30K–1L', '> ₹1L']
)

# Profit status
df['is_profitable'] = df['profit'] > 0

# Customer lifetime value (total spend per customer — for joining later)
clv = df.groupby('customer_id')['sales'].sum().reset_index()
clv.columns = ['customer_id', 'customer_ltv']
df = df.merge(clv, on='customer_id', how='left')

# Customer tier based on LTV
df['customer_tier'] = pd.cut(
    df['customer_ltv'],
    bins=[0, 50000, 150000, 300000, float('inf')],
    labels=['Bronze', 'Silver', 'Gold', 'Platinum']
)

# Revenue contribution per order
total_sales = df['sales'].sum()
df['revenue_share_pct'] = round(df['sales'] / total_sales * 100, 4)

print(f"  ✓ Date features: year, month, quarter, month_name, year_month")
print(f"  ✓ days_to_ship: {df['days_to_ship'].min()} – {df['days_to_ship'].max()} days")
print(f"  ✓ discount_band, sales_band, is_profitable")
print(f"  ✓ customer_ltv, customer_tier")

# ── 5. FINAL VALIDATION ───────────────────────────────────────────────────────
print("\n[VALIDATE] Final checks...")

assert df['order_date'].isna().sum() == 0, "Null order dates found"
assert df['sales'].min() >= 0,            "Negative sales found"
assert df['order_id'].nunique() == len(df),"Duplicate order IDs found"

print(f"  ✓ No null dates")
print(f"  ✓ No negative sales")
print(f"  ✓ All order IDs unique")

# ── 6. SUMMARY STATS ──────────────────────────────────────────────────────────
print("\n[SUMMARY] Cleaned dataset statistics:")
print(f"  Total records  : {len(df):,}")
print(f"  Date range     : {df['order_date'].min().date()} → {df['order_date'].max().date()}")
print(f"  Total sales    : ₹{df['sales'].sum():>15,.0f}")
print(f"  Total profit   : ₹{df['profit'].sum():>15,.0f}")
print(f"  Avg margin     : {df['profit_margin'].mean():.1f}%")
print(f"  Profitable orders: {df['is_profitable'].sum():,} / {len(df):,} ({df['is_profitable'].mean()*100:.1f}%)")
print(f"  Unique customers : {df['customer_id'].nunique()}")
print(f"  Unique products  : {df['product_name'].nunique()}")

# Category breakdown
print(f"\n  Category breakdown:")
cat_summary = df.groupby('category').agg(
    orders=('order_id','count'),
    revenue=('sales','sum'),
    profit=('profit','sum')
).reset_index()
cat_summary['margin'] = (cat_summary['profit'] / cat_summary['revenue'] * 100).round(1)
for _, row in cat_summary.iterrows():
    print(f"    {row['category']:<20} {row['orders']:>5} orders  "
          f"₹{row['revenue']:>12,.0f} sales  {row['margin']}% margin")

# ── 7. SAVE ───────────────────────────────────────────────────────────────────
df.to_csv(CLEAN_PATH, index=False)
print(f"\n[SAVE] Cleaned data → {CLEAN_PATH}")
print(f"  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

# Save quality report
report_lines.append(f"\n── ENGINEERED FEATURES ──────────────────────")
new_cols = ['order_year','order_month','order_quarter','order_month_name',
            'order_year_month','days_to_ship','discount_band','sales_band',
            'is_profitable','customer_ltv','customer_tier','revenue_share_pct']
for c in new_cols:
    report_lines.append(f"  + {c}")

report_lines.append(f"\n── FINAL SHAPE ──────────────────────────────")
report_lines.append(f"  {df.shape[0]:,} rows × {df.shape[1]} columns")
report_lines.append(f"\n  Cleaned file: {CLEAN_PATH}")

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))
print(f"[SAVE] Quality report → {REPORT_PATH}")

print("\n" + "=" * 60)
print("  Data cleaning complete. Run 02_eda.py next.")
print("=" * 60)
