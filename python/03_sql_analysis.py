"""
Step 3: SQL Analysis
=====================
Smart Sales Intelligence Dashboard
Author: Manya Kumar

What this script does:
- Loads cleaned data into a SQLite database
- Runs 15 business SQL queries covering:
    Basic aggregations, GROUP BY, HAVING
    Window functions (RANK, DENSE_RANK, ROW_NUMBER, LAG)
    CTEs (single and chained)
    Subqueries (correlated and non-correlated)
    CASE WHEN conditional aggregation
    Date functions
    JOINs (self-join pattern via CTE)
- Prints results and saves to outputs/reports/sql_results.txt
"""

import sqlite3
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH   = os.path.join(BASE_DIR, 'data', 'cleaned_sales_data.csv')
DB_PATH     = os.path.join(BASE_DIR, 'data', 'sales.db')
SQL_DIR     = os.path.join(BASE_DIR, 'sql')
REPORT_PATH = os.path.join(BASE_DIR, 'outputs', 'reports', 'sql_results.txt')

# ── LOAD INTO SQLITE ──────────────────────────────────────────────────────────
print("=" * 65)
print("  SMART SALES DASHBOARD -- SQL ANALYSIS")
print("=" * 65)

df = pd.read_csv(DATA_PATH)
conn = sqlite3.connect(DB_PATH)
df.to_sql('sales', conn, if_exists='replace', index=False)
print(f"\n[DB] Loaded {len(df):,} rows into SQLite: {DB_PATH}")
print(f"[DB] Table: 'sales'  |  Columns: {len(df.columns)}\n")

# ── QUERY RUNNER ──────────────────────────────────────────────────────────────
results_log = []

def run_query(qnum, title, sql, conn, show_rows=10):
    print(f"{'='*65}")
    print(f"  Q{qnum:02d} | {title}")
    print(f"{'='*65}")
    try:
        result = pd.read_sql_query(sql, conn)
        print(result.head(show_rows).to_string(index=False))
        if len(result) > show_rows:
            print(f"  ... ({len(result)} rows total, showing {show_rows})")
        print()
        results_log.append(f"\n{'='*65}\nQ{qnum:02d} | {title}\n{'='*65}")
        results_log.append(result.head(show_rows).to_string(index=False))
        results_log.append(f"({len(result)} total rows)\n")
        return result
    except Exception as e:
        print(f"  ERROR: {e}\n")
        results_log.append(f"ERROR in Q{qnum}: {e}\n")
        return None

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 01 — Basic: Revenue & Profit Summary by Category
# ══════════════════════════════════════════════════════════════════════════════
q01 = """
SELECT
    category,
    COUNT(order_id)                          AS total_orders,
    ROUND(SUM(sales), 0)                     AS total_revenue,
    ROUND(SUM(profit), 0)                    AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS profit_margin_pct,
    ROUND(AVG(sales), 0)                     AS avg_order_value
FROM sales
GROUP BY category
ORDER BY total_revenue DESC;
"""
run_query(1, "Revenue & Profit Summary by Category", q01, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 02 — HAVING: High-Value Customers (LTV > 200,000)
# ══════════════════════════════════════════════════════════════════════════════
q02 = """
SELECT
    customer_name,
    region,
    segment,
    COUNT(order_id)        AS total_orders,
    ROUND(SUM(sales), 0)   AS lifetime_value,
    ROUND(AVG(sales), 0)   AS avg_order_value,
    ROUND(SUM(profit), 0)  AS total_profit
FROM sales
GROUP BY customer_id, customer_name, region, segment
HAVING SUM(sales) > 200000
ORDER BY lifetime_value DESC;
"""
run_query(2, "High-Value Customers (LTV > Rs.2 Lakh)", q02, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 03 — Date Functions: Monthly Revenue Trend
# ══════════════════════════════════════════════════════════════════════════════
q03 = """
SELECT
    order_year                       AS year,
    order_month                      AS month,
    COUNT(order_id)                  AS orders,
    ROUND(SUM(sales), 0)             AS monthly_revenue,
    ROUND(AVG(sales), 0)             AS avg_order_value,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM sales
GROUP BY order_year, order_month
ORDER BY order_year, order_month;
"""
run_query(3, "Monthly Revenue Trend with Margin", q03, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 04 — Subquery: Products with Above-Average Profit Margin
# ══════════════════════════════════════════════════════════════════════════════
q04 = """
SELECT
    product_name,
    category,
    COUNT(order_id)                              AS orders,
    ROUND(SUM(sales), 0)                         AS total_sales,
    ROUND(AVG(profit_margin), 1)                 AS avg_margin_pct
FROM sales
GROUP BY product_name, category
HAVING AVG(profit_margin) > (
    SELECT AVG(profit_margin) FROM sales
)
ORDER BY avg_margin_pct DESC;
"""
run_query(4, "Products with Above-Average Profit Margin (Subquery)", q04, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 05 — Window Function: Rank Customers by Revenue within Region
# ══════════════════════════════════════════════════════════════════════════════
q05 = """
WITH customer_region AS (
    SELECT
        customer_name,
        region,
        ROUND(SUM(sales), 0)  AS total_sales,
        COUNT(order_id)        AS orders
    FROM sales
    GROUP BY customer_id, customer_name, region
),
ranked AS (
    SELECT
        customer_name,
        region,
        total_sales,
        orders,
        DENSE_RANK() OVER (
            PARTITION BY region
            ORDER BY total_sales DESC
        ) AS region_rank
    FROM customer_region
)
SELECT *
FROM ranked
WHERE region_rank <= 3
ORDER BY region, region_rank;
"""
run_query(5, "Top 3 Customers by Revenue per Region (DENSE_RANK)", q05, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 06 — Window Function: Month-over-Month Revenue Growth
# ══════════════════════════════════════════════════════════════════════════════
q06 = """
WITH monthly AS (
    SELECT
        order_year,
        order_month,
        ROUND(SUM(sales), 0) AS revenue
    FROM sales
    GROUP BY order_year, order_month
),
with_lag AS (
    SELECT
        order_year,
        order_month,
        revenue,
        LAG(revenue) OVER (ORDER BY order_year, order_month) AS prev_revenue
    FROM monthly
)
SELECT
    order_year,
    order_month,
    revenue,
    prev_revenue,
    ROUND((revenue - prev_revenue) * 100.0 / prev_revenue, 1) AS mom_growth_pct
FROM with_lag
WHERE prev_revenue IS NOT NULL
ORDER BY order_year, order_month;
"""
run_query(6, "Month-over-Month Revenue Growth (LAG Window Function)", q06, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 07 — CTE + ROW_NUMBER: Best Selling Product per Category
# ══════════════════════════════════════════════════════════════════════════════
q07 = """
WITH product_sales AS (
    SELECT
        category,
        product_name,
        ROUND(SUM(sales), 0)  AS total_sales,
        COUNT(order_id)        AS orders,
        ROUND(SUM(profit), 0)  AS total_profit
    FROM sales
    GROUP BY category, product_name
),
ranked AS (
    SELECT
        category,
        product_name,
        total_sales,
        orders,
        total_profit,
        ROW_NUMBER() OVER (
            PARTITION BY category
            ORDER BY total_sales DESC
        ) AS rnk
    FROM product_sales
)
SELECT category, product_name, total_sales, orders, total_profit
FROM ranked
WHERE rnk = 1
ORDER BY total_sales DESC;
"""
run_query(7, "Best Selling Product per Category (ROW_NUMBER + CTE)", q07, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 08 — CASE WHEN: Discount Impact Segmentation
# ══════════════════════════════════════════════════════════════════════════════
q08 = """
SELECT
    CASE
        WHEN discount = 0          THEN 'No Discount'
        WHEN discount <= 0.10      THEN 'Low (1-10%)'
        WHEN discount <= 0.20      THEN 'Medium (11-20%)'
        WHEN discount <= 0.30      THEN 'High (21-30%)'
        ELSE                            'Very High (>30%)'
    END                                          AS discount_band,
    COUNT(order_id)                              AS orders,
    ROUND(SUM(sales), 0)                         AS total_revenue,
    ROUND(AVG(profit_margin), 1)                 AS avg_margin_pct,
    ROUND(AVG(profit), 0)                        AS avg_profit_per_order,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 1)  AS effective_margin
FROM sales
GROUP BY discount_band
ORDER BY
    CASE discount_band
        WHEN 'No Discount'      THEN 1
        WHEN 'Low (1-10%)'     THEN 2
        WHEN 'Medium (11-20%)' THEN 3
        WHEN 'High (21-30%)'   THEN 4
        ELSE 5
    END;
"""
run_query(8, "Discount Band Impact on Profitability (CASE WHEN)", q08, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 09 — Correlated Subquery: Customers Above Their Segment Average
# ══════════════════════════════════════════════════════════════════════════════
q09 = """
SELECT
    a.customer_name,
    a.segment,
    a.region,
    ROUND(SUM(a.sales), 0) AS customer_revenue,
    ROUND((
        SELECT AVG(b.sales)
        FROM sales b
        WHERE b.segment = a.segment
    ), 0)                  AS segment_avg_order_value
FROM sales a
GROUP BY a.customer_id, a.customer_name, a.segment, a.region
HAVING SUM(a.sales) > 3 * (
    SELECT AVG(b.sales)
    FROM sales b
    WHERE b.segment = a.segment
)
ORDER BY customer_revenue DESC
LIMIT 15;
"""
run_query(9, "Customers Spending 3x Their Segment Average (Correlated Subquery)", q09, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 10 — Running Total: Cumulative Revenue by Month
# ══════════════════════════════════════════════════════════════════════════════
q10 = """
WITH monthly AS (
    SELECT
        order_year,
        order_month,
        ROUND(SUM(sales), 0) AS monthly_revenue
    FROM sales
    GROUP BY order_year, order_month
)
SELECT
    order_year,
    order_month,
    monthly_revenue,
    ROUND(SUM(monthly_revenue) OVER (
        PARTITION BY order_year
        ORDER BY order_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 0) AS cumulative_revenue_ytd
FROM monthly
ORDER BY order_year, order_month;
"""
run_query(10, "Cumulative YTD Revenue per Month (Running Total)", q10, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 11 — Chained CTEs: Regional Performance Scorecard
# ══════════════════════════════════════════════════════════════════════════════
q11 = """
WITH regional_metrics AS (
    SELECT
        region,
        COUNT(DISTINCT customer_id)              AS unique_customers,
        COUNT(order_id)                          AS total_orders,
        ROUND(SUM(sales), 0)                     AS total_revenue,
        ROUND(SUM(profit), 0)                    AS total_profit,
        ROUND(AVG(sales), 0)                     AS avg_order_value
    FROM sales
    GROUP BY region
),
with_margin AS (
    SELECT
        *,
        ROUND(total_profit * 100.0 / total_revenue, 1) AS margin_pct,
        ROUND(total_revenue * 1.0 / unique_customers, 0) AS revenue_per_customer
    FROM regional_metrics
),
ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY total_revenue DESC)   AS revenue_rank,
        RANK() OVER (ORDER BY margin_pct DESC)       AS margin_rank
    FROM with_margin
)
SELECT
    region,
    unique_customers,
    total_orders,
    total_revenue,
    total_profit,
    margin_pct,
    avg_order_value,
    revenue_per_customer,
    revenue_rank,
    margin_rank
FROM ranked
ORDER BY revenue_rank;
"""
run_query(11, "Regional Performance Scorecard (Chained CTEs + RANK)", q11, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 12 — Year-over-Year Growth by Category
# ══════════════════════════════════════════════════════════════════════════════
q12 = """
WITH yearly AS (
    SELECT
        order_year,
        category,
        ROUND(SUM(sales), 0) AS revenue
    FROM sales
    GROUP BY order_year, category
),
with_prev AS (
    SELECT
        order_year,
        category,
        revenue,
        LAG(revenue) OVER (
            PARTITION BY category
            ORDER BY order_year
        ) AS prev_year_revenue
    FROM yearly
)
SELECT
    order_year,
    category,
    revenue,
    prev_year_revenue,
    ROUND((revenue - prev_year_revenue) * 100.0 / prev_year_revenue, 1) AS yoy_growth_pct
FROM with_prev
WHERE prev_year_revenue IS NOT NULL
ORDER BY category, order_year;
"""
run_query(12, "Year-over-Year Revenue Growth by Category (LAG + PARTITION)", q12, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 13 — INTERSECT: Customers Who Ordered in Both 2022 and 2024
# ══════════════════════════════════════════════════════════════════════════════
q13 = """
SELECT customer_name, region, segment
FROM sales
WHERE order_year = 2022
  AND customer_id IN (
      SELECT DISTINCT customer_id FROM sales WHERE order_year = 2022
      INTERSECT
      SELECT DISTINCT customer_id FROM sales WHERE order_year = 2024
  )
GROUP BY customer_id, customer_name, region, segment
ORDER BY customer_name
LIMIT 15;
"""
run_query(13, "Retained Customers: Ordered in Both 2022 and 2024 (INTERSECT)", q13, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 14 — FIRST_VALUE / LAST_VALUE: First vs Latest Order per Customer
# ══════════════════════════════════════════════════════════════════════════════
q14 = """
WITH order_values AS (
    SELECT
        customer_name,
        region,
        sales,
        order_date,
        FIRST_VALUE(sales) OVER (
            PARTITION BY customer_id
            ORDER BY order_date ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS first_order_value,
        FIRST_VALUE(sales) OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS latest_order_value
    FROM sales
)
SELECT DISTINCT
    customer_name,
    region,
    ROUND(first_order_value, 0)  AS first_order_value,
    ROUND(latest_order_value, 0) AS latest_order_value,
    ROUND(latest_order_value - first_order_value, 0) AS value_change
FROM order_values
ORDER BY value_change DESC
LIMIT 15;
"""
run_query(14, "First vs Latest Order Value per Customer (FIRST_VALUE)", q14, conn)

# ══════════════════════════════════════════════════════════════════════════════
#  QUERY 15 — Complex: Quarterly Sales Pivot with CASE WHEN
# ══════════════════════════════════════════════════════════════════════════════
q15 = """
SELECT
    order_year,
    category,
    ROUND(SUM(CASE WHEN order_quarter = 1 THEN sales ELSE 0 END), 0) AS Q1,
    ROUND(SUM(CASE WHEN order_quarter = 2 THEN sales ELSE 0 END), 0) AS Q2,
    ROUND(SUM(CASE WHEN order_quarter = 3 THEN sales ELSE 0 END), 0) AS Q3,
    ROUND(SUM(CASE WHEN order_quarter = 4 THEN sales ELSE 0 END), 0) AS Q4,
    ROUND(SUM(sales), 0)                                              AS annual_total,
    ROUND(
        (SUM(CASE WHEN order_quarter = 4 THEN sales ELSE 0 END) -
         SUM(CASE WHEN order_quarter = 1 THEN sales ELSE 0 END))
        * 100.0 /
        NULLIF(SUM(CASE WHEN order_quarter = 1 THEN sales ELSE 0 END), 0)
    , 1)                                                              AS q4_vs_q1_growth_pct
FROM sales
GROUP BY order_year, category
ORDER BY order_year, annual_total DESC;
"""
run_query(15, "Quarterly Sales Pivot by Category (CASE WHEN Conditional Aggregation)", q15, conn)

# ── SAVE FULL QUERY FILE ──────────────────────────────────────────────────────
all_queries = {
    "Q01_category_summary":       q01,
    "Q02_high_value_customers":   q02,
    "Q03_monthly_trend":          q03,
    "Q04_above_avg_margin":       q04,
    "Q05_top_customers_region":   q05,
    "Q06_mom_growth":             q06,
    "Q07_best_product_category":  q07,
    "Q08_discount_impact":        q08,
    "Q09_correlated_subquery":    q09,
    "Q10_running_total":          q10,
    "Q11_regional_scorecard":     q11,
    "Q12_yoy_growth":             q12,
    "Q13_retained_customers":     q13,
    "Q14_first_vs_latest":        q14,
    "Q15_quarterly_pivot":        q15,
}

sql_file = os.path.join(SQL_DIR, 'analysis_queries.sql')
with open(sql_file, 'w', encoding='utf-8') as f:
    f.write("-- ============================================================\n")
    f.write("-- Smart Sales Intelligence Dashboard -- SQL Analysis Queries\n")
    f.write("-- Author: Manya Kumar\n")
    f.write("-- Database: SQLite (sales.db) | Table: sales\n")
    f.write("-- 15 Queries covering: aggregations, window functions,\n")
    f.write("--   CTEs, subqueries, CASE WHEN, date functions, INTERSECT\n")
    f.write("-- ============================================================\n\n")
    for name, sql in all_queries.items():
        f.write(f"-- {'-'*58}\n")
        f.write(f"-- {name}\n")
        f.write(f"-- {'-'*58}\n")
        f.write(sql.strip() + ";\n\n")

print(f"[SAVE] SQL queries --> {sql_file}")

# Save results
with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write("Smart Sales Dashboard -- SQL Query Results\n")
    f.write("=" * 65 + "\n")
    f.write('\n'.join(results_log))
print(f"[SAVE] SQL results --> {REPORT_PATH}")

conn.close()
print("\n" + "=" * 65)
print("  SQL analysis complete. 15 queries run and saved.")
print("  Database: data/sales.db")
print("  Queries:  sql/analysis_queries.sql")
print("=" * 65)
