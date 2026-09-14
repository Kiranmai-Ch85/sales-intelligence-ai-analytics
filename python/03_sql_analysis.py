"""
Step 3: SQL Analysis
=====================
Smart Sales Intelligence Dashboard

This script:
1. Loads the cleaned data into a SQLite database
2. Runs business SQL queries on it
3. Prints the results

The queries use GROUP BY, HAVING, window functions (RANK, LAG,
ROW_NUMBER, FIRST_VALUE), CTEs, subqueries and CASE WHEN.
"""

import sqlite3
import pandas as pd

# ---- 1. Load data into SQLite ----
df = pd.read_csv("../data/cleaned_sales_data.csv")

# Create a database connection and write the data into a table called "sales"
conn = sqlite3.connect("../data/sales.db")
df.to_sql("sales", conn, if_exists="replace", index=False)
print("Loaded", len(df), "rows into the 'sales' table\n")


# ---- 2. Write the queries ----
# Each query is stored as a string with a short title.

queries = {}

# Q1: Revenue and profit summary by category
queries["Q1 - Category Summary"] = """
SELECT category,
       COUNT(order_id) AS total_orders,
       ROUND(SUM(sales)) AS total_revenue,
       ROUND(SUM(profit)) AS total_profit,
       ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM sales
GROUP BY category
ORDER BY total_revenue DESC;
"""

# Q2: High value customers (lifetime spend over 2 lakh)
queries["Q2 - High Value Customers"] = """
SELECT customer_name, region, segment,
       COUNT(order_id) AS orders,
       ROUND(SUM(sales)) AS lifetime_value
FROM sales
GROUP BY customer_id, customer_name, region, segment
HAVING SUM(sales) > 200000
ORDER BY lifetime_value DESC
LIMIT 10;
"""

# Q3: Monthly revenue trend
queries["Q3 - Monthly Trend"] = """
SELECT order_year, order_month,
       COUNT(order_id) AS orders,
       ROUND(SUM(sales)) AS monthly_revenue
FROM sales
GROUP BY order_year, order_month
ORDER BY order_year, order_month
LIMIT 12;
"""

# Q4: Products with above-average profit margin (uses a subquery)
queries["Q4 - Above Average Margin Products"] = """
SELECT product_name, category,
       ROUND(AVG(profit_margin), 1) AS avg_margin
FROM sales
GROUP BY product_name, category
HAVING AVG(profit_margin) > (SELECT AVG(profit_margin) FROM sales)
ORDER BY avg_margin DESC
LIMIT 10;
"""

# Q5: Top 3 customers by revenue in each region (window function + CTE)
queries["Q5 - Top 3 Customers per Region"] = """
WITH customer_totals AS (
    SELECT customer_name, region,
           ROUND(SUM(sales)) AS total_sales
    FROM sales
    GROUP BY customer_id, customer_name, region
)
SELECT customer_name, region, total_sales, region_rank
FROM (
    SELECT customer_name, region, total_sales,
           DENSE_RANK() OVER (PARTITION BY region ORDER BY total_sales DESC) AS region_rank
    FROM customer_totals
)
WHERE region_rank <= 3
ORDER BY region, region_rank;
"""

# Q6: Month over month revenue growth (LAG)
queries["Q6 - Month over Month Growth"] = """
WITH monthly AS (
    SELECT order_year, order_month, ROUND(SUM(sales)) AS revenue
    FROM sales
    GROUP BY order_year, order_month
)
SELECT order_year, order_month, revenue,
       LAG(revenue) OVER (ORDER BY order_year, order_month) AS prev_revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY order_year, order_month))
             * 100.0 / LAG(revenue) OVER (ORDER BY order_year, order_month), 1) AS growth_pct
FROM monthly
LIMIT 12;
"""

# Q7: Best selling product in each category (ROW_NUMBER)
queries["Q7 - Best Product per Category"] = """
WITH product_sales AS (
    SELECT category, product_name, ROUND(SUM(sales)) AS total_sales
    FROM sales
    GROUP BY category, product_name
)
SELECT category, product_name, total_sales
FROM (
    SELECT category, product_name, total_sales,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY total_sales DESC) AS rnk
    FROM product_sales
)
WHERE rnk = 1
ORDER BY total_sales DESC;
"""

# Q8: Discount impact on profit (CASE WHEN)
queries["Q8 - Discount Impact"] = """
SELECT
    CASE
        WHEN discount = 0 THEN 'No Discount'
        WHEN discount <= 0.10 THEN 'Low (1-10%)'
        WHEN discount <= 0.20 THEN 'Medium (11-20%)'
        WHEN discount <= 0.30 THEN 'High (21-30%)'
        ELSE 'Very High (>30%)'
    END AS discount_band,
    COUNT(order_id) AS orders,
    ROUND(AVG(profit_margin), 1) AS avg_margin
FROM sales
GROUP BY discount_band
ORDER BY avg_margin DESC;
"""

# Q9: Running total of revenue within each year (window function)
queries["Q9 - Cumulative Revenue (Running Total)"] = """
WITH monthly AS (
    SELECT order_year, order_month, ROUND(SUM(sales)) AS revenue
    FROM sales
    GROUP BY order_year, order_month
)
SELECT order_year, order_month, revenue,
       SUM(revenue) OVER (PARTITION BY order_year ORDER BY order_month) AS running_total
FROM monthly
LIMIT 12;
"""

# Q10: Quarterly sales pivot by category (CASE WHEN)
queries["Q10 - Quarterly Pivot"] = """
SELECT order_year, category,
       ROUND(SUM(CASE WHEN order_quarter = 1 THEN sales ELSE 0 END)) AS Q1,
       ROUND(SUM(CASE WHEN order_quarter = 2 THEN sales ELSE 0 END)) AS Q2,
       ROUND(SUM(CASE WHEN order_quarter = 3 THEN sales ELSE 0 END)) AS Q3,
       ROUND(SUM(CASE WHEN order_quarter = 4 THEN sales ELSE 0 END)) AS Q4
FROM sales
GROUP BY order_year, category
ORDER BY order_year
LIMIT 10;
"""


# ---- 3. Run each query and print the result ----
for title, query in queries.items():
    print("=" * 60)
    print(title)
    print("=" * 60)
    result = pd.read_sql_query(query, conn)
    print(result.to_string(index=False))
    print()

conn.close()
print("SQL analysis complete. Database saved to data/sales.db")
