"""
Power BI Data Preparation
==========================
Smart Sales Intelligence Dashboard
Author: Manya Kumar

Builds a clean STAR SCHEMA for Power BI:
  - fact_sales.csv        (transaction-level facts)
  - dim_customer.csv      (customer dimension)
  - dim_product.csv       (product dimension)
  - dim_date.csv          (date dimension / calendar table)
  - dim_geography.csv     (region + city dimension)

Star schema is the industry-standard model for BI tools.
It makes relationships clean and DAX measures simple.
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, 'data', 'cleaned_sales_data.csv')
PBI_DIR    = os.path.join(BASE_DIR, 'powerbi', 'data_model')
os.makedirs(PBI_DIR, exist_ok=True)

print("=" * 60)
print("  POWER BI -- STAR SCHEMA DATA PREPARATION")
print("=" * 60)

df = pd.read_csv(DATA_PATH, parse_dates=['order_date', 'ship_date'])
print(f"\n[LOAD] {len(df):,} rows")

# ── DIM_CUSTOMER ──────────────────────────────────────────────────────────────
print("[BUILD] dim_customer...")
dim_customer = df.groupby('customer_id').agg(
    customer_name=('customer_name', 'first'),
    segment=('segment', 'first'),
    customer_tier=('customer_tier', 'first'),
    customer_ltv=('customer_ltv', 'first'),
    home_region=('region', 'first'),
    home_city=('city', 'first'),
    total_orders=('order_id', 'count'),
).reset_index()
dim_customer.to_csv(os.path.join(PBI_DIR, 'dim_customer.csv'), index=False)
print(f"         {len(dim_customer)} customers")

# ── DIM_PRODUCT ───────────────────────────────────────────────────────────────
print("[BUILD] dim_product...")
dim_product = df.groupby('product_name').agg(
    category=('category', 'first'),
    avg_unit_price=('unit_price', 'mean'),
).reset_index()
dim_product['product_id'] = ['PROD-' + str(i+1).zfill(3) for i in range(len(dim_product))]
dim_product['avg_unit_price'] = dim_product['avg_unit_price'].round(2)
dim_product = dim_product[['product_id', 'product_name', 'category', 'avg_unit_price']]
dim_product.to_csv(os.path.join(PBI_DIR, 'dim_product.csv'), index=False)
print(f"         {len(dim_product)} products")

# ── DIM_GEOGRAPHY ─────────────────────────────────────────────────────────────
print("[BUILD] dim_geography...")
dim_geo = df.groupby(['region', 'city']).size().reset_index(name='order_count')
dim_geo['geo_id'] = ['GEO-' + str(i+1).zfill(3) for i in range(len(dim_geo))]
dim_geo = dim_geo[['geo_id', 'region', 'city', 'order_count']]
dim_geo.to_csv(os.path.join(PBI_DIR, 'dim_geography.csv'), index=False)
print(f"         {len(dim_geo)} region-city pairs")

# ── DIM_DATE (Calendar Table) ─────────────────────────────────────────────────
print("[BUILD] dim_date (calendar table)...")
date_range = pd.date_range(df['order_date'].min(), df['order_date'].max(), freq='D')
dim_date = pd.DataFrame({'date': date_range})
dim_date['date_key']     = dim_date['date'].dt.strftime('%Y%m%d').astype(int)
dim_date['year']         = dim_date['date'].dt.year
dim_date['quarter']      = dim_date['date'].dt.quarter
dim_date['quarter_name'] = 'Q' + dim_date['quarter'].astype(str)
dim_date['month']        = dim_date['date'].dt.month
dim_date['month_name']   = dim_date['date'].dt.strftime('%B')
dim_date['month_short']  = dim_date['date'].dt.strftime('%b')
dim_date['year_month']   = dim_date['date'].dt.strftime('%Y-%m')
dim_date['week']         = dim_date['date'].dt.isocalendar().week.astype(int)
dim_date['day']          = dim_date['date'].dt.day
dim_date['day_name']     = dim_date['date'].dt.strftime('%A')
dim_date['is_weekend']   = dim_date['date'].dt.dayofweek >= 5
dim_date['is_festive_q'] = dim_date['quarter'] == 4
dim_date['date']         = dim_date['date'].dt.strftime('%Y-%m-%d')
dim_date.to_csv(os.path.join(PBI_DIR, 'dim_date.csv'), index=False)
print(f"         {len(dim_date)} dates ({dim_date['year'].min()}-{dim_date['year'].max()})")

# ── FACT_SALES ────────────────────────────────────────────────────────────────
print("[BUILD] fact_sales...")
# Merge product_id and geo_id into fact table
prod_map = dim_product.set_index('product_name')['product_id'].to_dict()
geo_map  = dim_geo.set_index(['region', 'city'])['geo_id'].to_dict()

fact = df.copy()
fact['product_id'] = fact['product_name'].map(prod_map)
fact['geo_id']     = fact.apply(lambda r: geo_map.get((r['region'], r['city'])), axis=1)
fact['date_key']   = pd.to_datetime(fact['order_date']).dt.strftime('%Y%m%d').astype(int)

fact_sales = fact[[
    'order_id', 'date_key', 'customer_id', 'product_id', 'geo_id',
    'ship_mode', 'quantity', 'unit_price', 'discount',
    'sales', 'profit', 'profit_margin', 'days_to_ship'
]].copy()
fact_sales.to_csv(os.path.join(PBI_DIR, 'fact_sales.csv'), index=False)
print(f"         {len(fact_sales):,} fact rows")

# Also save a single flat file for quick-start (denormalized)
print("[BUILD] flat_sales (denormalized single-file option)...")
df.to_csv(os.path.join(PBI_DIR, 'flat_sales.csv'), index=False)
print(f"         {len(df):,} rows (all columns)")

print("\n" + "=" * 60)
print("  STAR SCHEMA READY for Power BI import")
print("=" * 60)
print("""
  Files created in powerbi/data_model/:
    fact_sales.csv       <- central fact table
    dim_customer.csv     <- link on customer_id
    dim_product.csv      <- link on product_id
    dim_geography.csv    <- link on geo_id
    dim_date.csv         <- link date_key (mark as Date Table)
    flat_sales.csv       <- OR use this single file for quick start

  RELATIONSHIPS to create in Power BI Model view:
    fact_sales[customer_id] --> dim_customer[customer_id]
    fact_sales[product_id]  --> dim_product[product_id]
    fact_sales[geo_id]      --> dim_geography[geo_id]
    fact_sales[date_key]    --> dim_date[date_key]
""")
