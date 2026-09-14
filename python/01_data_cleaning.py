"""
Step 1: Data Cleaning & Feature Engineering
============================================
Smart Sales Intelligence Dashboard

This script:
1. Loads the raw sales data
2. Checks for nulls and duplicates
3. Fixes data types (dates)
4. Creates new useful columns (feature engineering)
5. Saves the cleaned data
"""

import pandas as pd

# ---- 1. Load the data ----
df = pd.read_csv("../data/raw_sales_data.csv")
print("Rows and columns:", df.shape)
print(df.head())


# ---- 2. Check data quality ----

# Check for missing values in each column
print("\nMissing values per column:")
print(df.isnull().sum())

# Check for duplicate rows
print("\nDuplicate rows:", df.duplicated().sum())

# Remove duplicates if any
df = df.drop_duplicates()

# Look at data types
print("\nData types:")
print(df.dtypes)


# ---- 3. Fix data types ----
# The date columns are read as text, so convert them to datetime
df["order_date"] = pd.to_datetime(df["order_date"])
df["ship_date"] = pd.to_datetime(df["ship_date"])


# ---- 4. Feature engineering (create new columns) ----

# Break the order date into year, month and quarter for trend analysis
df["order_year"] = df["order_date"].dt.year
df["order_month"] = df["order_date"].dt.month
df["order_quarter"] = df["order_date"].dt.quarter
df["order_month_name"] = df["order_date"].dt.strftime("%b")   # Jan, Feb...
df["order_year_month"] = df["order_date"].dt.strftime("%Y-%m")  # 2021-01

# How many days it took to ship the order
df["days_to_ship"] = (df["ship_date"] - df["order_date"]).dt.days

# Group discounts into bands so we can compare their effect on profit
df["discount_band"] = pd.cut(
    df["discount"],
    bins=[-0.01, 0.0, 0.10, 0.20, 0.30, 1.0],
    labels=["No Discount", "Low (1-10%)", "Medium (11-20%)",
            "High (21-30%)", "Very High (>30%)"]
)

# Group order value into bands
df["sales_band"] = pd.cut(
    df["sales"],
    bins=[0, 2000, 10000, 30000, 100000, float("inf")],
    labels=["< 2K", "2K-10K", "10K-30K", "30K-1L", "> 1L"]
)

# A simple True/False column for whether the order made a profit
df["is_profitable"] = df["profit"] > 0

# Customer Lifetime Value = total money each customer has spent
# Step 1: find total sales per customer
customer_ltv = df.groupby("customer_id")["sales"].sum()
# Step 2: map that total back to every row of that customer
df["customer_ltv"] = df["customer_id"].map(customer_ltv)

# Group customers into tiers based on how much they spent
df["customer_tier"] = pd.cut(
    df["customer_ltv"],
    bins=[0, 50000, 150000, 300000, float("inf")],
    labels=["Bronze", "Silver", "Gold", "Platinum"]
)


# ---- 5. Quick summary ----
print("\n--- Summary after cleaning ---")
print("Total rows:", len(df))
print("Total columns:", len(df.columns))
print("Date range:", df["order_date"].min().date(), "to", df["order_date"].max().date())
print("Total sales:", round(df["sales"].sum()))
print("Total profit:", round(df["profit"].sum()))
print("Unique customers:", df["customer_id"].nunique())
print("Unique products:", df["product_name"].nunique())

# Sales and profit by category
print("\nCategory breakdown:")
category_summary = df.groupby("category")[["sales", "profit"]].sum()
print(category_summary)


# ---- 6. Save the cleaned data ----
df.to_csv("../data/cleaned_sales_data.csv", index=False)
print("\nCleaned data saved to data/cleaned_sales_data.csv")
