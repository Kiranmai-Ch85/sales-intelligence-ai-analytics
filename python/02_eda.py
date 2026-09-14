"""
Step 2: Exploratory Data Analysis (EDA) & Visualizations
=========================================================
Smart Sales Intelligence Dashboard

This script reads the cleaned data and creates charts to explore:
- Monthly revenue trend
- Category performance
- Regional performance
- Discount impact on profit
- Top customers and products
- Customer segments
- Correlation between numeric columns

All charts are saved as PNG files in outputs/plots/.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---- Setup ----
sns.set_style("whitegrid")

PLOTS_DIR = "../outputs/plots/"

# ---- Load cleaned data ----
df = pd.read_csv("../data/cleaned_sales_data.csv", parse_dates=["order_date", "ship_date"])
print("Loaded", len(df), "rows")


# ---- Chart 1: Monthly revenue trend ----
monthly = df.groupby("order_year_month")["sales"].sum()

plt.figure(figsize=(12, 5))
plt.plot(monthly.index, monthly.values, marker="o", color="#2196F3")
plt.title("Monthly Revenue Trend (2021-2024)")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(PLOTS_DIR + "01_revenue_trend.png", dpi=150)
plt.close()
print("Saved 01_revenue_trend.png")


# ---- Chart 2: Revenue and profit by category ----
category = df.groupby("category")[["sales", "profit"]].sum().sort_values("sales", ascending=False)

plt.figure(figsize=(10, 5))
category.plot(kind="bar", color=["#2196F3", "#4CAF50"])
plt.title("Revenue and Profit by Category")
plt.ylabel("Amount")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(PLOTS_DIR + "02_category_performance.png", dpi=150)
plt.close()
print("Saved 02_category_performance.png")


# ---- Chart 3: Revenue share by region (pie) ----
region_sales = df.groupby("region")["sales"].sum()

plt.figure(figsize=(7, 7))
plt.pie(region_sales, labels=region_sales.index, autopct="%1.1f%%", startangle=90)
plt.title("Revenue Share by Region")
plt.tight_layout()
plt.savefig(PLOTS_DIR + "03_regional_analysis.png", dpi=150)
plt.close()
print("Saved 03_regional_analysis.png")


# ---- Chart 4: Discount impact on profit margin ----
# Order the bands correctly
band_order = ["No Discount", "Low (1-10%)", "Medium (11-20%)",
              "High (21-30%)", "Very High (>30%)"]
discount = df.groupby("discount_band")["profit_margin"].mean().reindex(band_order)

plt.figure(figsize=(9, 5))
discount.plot(kind="bar", color="#FF9800")
plt.title("Average Profit Margin by Discount Band")
plt.xlabel("Discount Band")
plt.ylabel("Avg Profit Margin (%)")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(PLOTS_DIR + "04_discount_impact.png", dpi=150)
plt.close()
print("Saved 04_discount_impact.png")


# ---- Chart 5: Top 10 customers by total sales ----
top_customers = df.groupby("customer_name")["sales"].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(10, 5))
top_customers.sort_values().plot(kind="barh", color="#9C27B0")
plt.title("Top 10 Customers by Total Revenue")
plt.xlabel("Total Revenue")
plt.tight_layout()
plt.savefig(PLOTS_DIR + "05_top_customers.png", dpi=150)
plt.close()
print("Saved 05_top_customers.png")


# ---- Chart 6: Top 10 products by profit ----
top_products = df.groupby("product_name")["profit"].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(10, 5))
top_products.sort_values().plot(kind="barh", color="#4CAF50")
plt.title("Top 10 Products by Profit")
plt.xlabel("Total Profit")
plt.tight_layout()
plt.savefig(PLOTS_DIR + "06_product_profitability.png", dpi=150)
plt.close()
print("Saved 06_product_profitability.png")


# ---- Chart 7: Orders by shipping mode ----
ship = df["ship_mode"].value_counts()

plt.figure(figsize=(8, 5))
ship.plot(kind="bar", color="#2196F3")
plt.title("Number of Orders by Shipping Mode")
plt.xlabel("Ship Mode")
plt.ylabel("Order Count")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(PLOTS_DIR + "07_shipping_analysis.png", dpi=150)
plt.close()
print("Saved 07_shipping_analysis.png")


# ---- Chart 8: Revenue by customer segment ----
segment = df.groupby("segment")["sales"].sum()

plt.figure(figsize=(8, 5))
segment.plot(kind="bar", color=["#1565C0", "#2E7D32", "#E65100"])
plt.title("Revenue by Customer Segment")
plt.ylabel("Revenue")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(PLOTS_DIR + "08_customer_segments.png", dpi=150)
plt.close()
print("Saved 08_customer_segments.png")


# ---- Chart 9: Quarterly revenue heatmap (year vs quarter) ----
heat = df.groupby(["order_quarter", "order_year"])["sales"].sum().unstack()

plt.figure(figsize=(9, 5))
sns.heatmap(heat, annot=True, fmt=".0f", cmap="YlOrRd")
plt.title("Revenue Heatmap: Quarter vs Year")
plt.xlabel("Year")
plt.ylabel("Quarter")
plt.tight_layout()
plt.savefig(PLOTS_DIR + "09_quarterly_heatmap.png", dpi=150)
plt.close()
print("Saved 09_quarterly_heatmap.png")


# ---- Chart 10: Yearly revenue by category ----
yearly = df.groupby(["order_year", "category"])["sales"].sum().unstack()

plt.figure(figsize=(10, 5))
yearly.plot(kind="line", marker="o")
plt.title("Yearly Revenue by Category")
plt.xlabel("Year")
plt.ylabel("Revenue")
plt.tight_layout()
plt.savefig(PLOTS_DIR + "10_yoy_growth.png", dpi=150)
plt.close()
print("Saved 10_yoy_growth.png")


# ---- Chart 11: Correlation heatmap of numeric columns ----
numeric_cols = ["quantity", "unit_price", "discount", "sales", "profit",
                "profit_margin", "days_to_ship", "customer_ltv"]
corr = df[numeric_cols].corr()

plt.figure(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.title("Correlation Between Numeric Features")
plt.tight_layout()
plt.savefig(PLOTS_DIR + "11_correlation_matrix.png", dpi=150)
plt.close()
print("Saved 11_correlation_matrix.png")


# ---- Print a few key insights ----
print("\n--- Key Insights ---")

total_revenue = df["sales"].sum()
total_profit = df["profit"].sum()
print("Total revenue:", round(total_revenue))
print("Total profit:", round(total_profit))
print("Overall profit margin:", round(total_profit / total_revenue * 100, 1), "%")

# Category with highest revenue and its margin
cat_stats = df.groupby("category").agg(
    revenue=("sales", "sum"),
    profit=("profit", "sum")
)
cat_stats["margin"] = (cat_stats["profit"] / cat_stats["revenue"] * 100).round(1)
print("\nCategory revenue and margin:")
print(cat_stats.sort_values("revenue", ascending=False))

# Q4 contribution
q4_revenue = df[df["order_quarter"] == 4]["sales"].sum()
print("\nQ4 revenue share:", round(q4_revenue / total_revenue * 100, 1), "%")

# Discount effect
print("\nAvg profit margin by discount band:")
print(df.groupby("discount_band")["profit_margin"].mean().reindex(band_order).round(1))

print("\nEDA complete. 11 charts saved to outputs/plots/")
