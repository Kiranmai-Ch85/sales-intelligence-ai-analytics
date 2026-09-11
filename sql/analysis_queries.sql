-- ============================================================
-- Smart Sales Intelligence Dashboard -- SQL Analysis Queries
-- Author: Manya Kumar
-- Database: SQLite (sales.db) | Table: sales
-- 15 Queries covering: aggregations, window functions,
--   CTEs, subqueries, CASE WHEN, date functions, INTERSECT
-- ============================================================

-- ----------------------------------------------------------
-- Q01_category_summary
-- ----------------------------------------------------------
SELECT
    category,
    COUNT(order_id)                          AS total_orders,
    ROUND(SUM(sales), 0)                     AS total_revenue,
    ROUND(SUM(profit), 0)                    AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS profit_margin_pct,
    ROUND(AVG(sales), 0)                     AS avg_order_value
FROM sales
GROUP BY category
ORDER BY total_revenue DESC;;

-- ----------------------------------------------------------
-- Q02_high_value_customers
-- ----------------------------------------------------------
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
ORDER BY lifetime_value DESC;;

-- ----------------------------------------------------------
-- Q03_monthly_trend
-- ----------------------------------------------------------
SELECT
    order_year                       AS year,
    order_month                      AS month,
    COUNT(order_id)                  AS orders,
    ROUND(SUM(sales), 0)             AS monthly_revenue,
    ROUND(AVG(sales), 0)             AS avg_order_value,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 1) AS margin_pct
FROM sales
GROUP BY order_year, order_month
ORDER BY order_year, order_month;;

-- ----------------------------------------------------------
-- Q04_above_avg_margin
-- ----------------------------------------------------------
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
ORDER BY avg_margin_pct DESC;;

-- ----------------------------------------------------------
-- Q05_top_customers_region
-- ----------------------------------------------------------
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
ORDER BY region, region_rank;;

-- ----------------------------------------------------------
-- Q06_mom_growth
-- ----------------------------------------------------------
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
ORDER BY order_year, order_month;;

-- ----------------------------------------------------------
-- Q07_best_product_category
-- ----------------------------------------------------------
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
ORDER BY total_sales DESC;;

-- ----------------------------------------------------------
-- Q08_discount_impact
-- ----------------------------------------------------------
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
    END;;

-- ----------------------------------------------------------
-- Q09_correlated_subquery
-- ----------------------------------------------------------
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
LIMIT 15;;

-- ----------------------------------------------------------
-- Q10_running_total
-- ----------------------------------------------------------
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
ORDER BY order_year, order_month;;

-- ----------------------------------------------------------
-- Q11_regional_scorecard
-- ----------------------------------------------------------
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
ORDER BY revenue_rank;;

-- ----------------------------------------------------------
-- Q12_yoy_growth
-- ----------------------------------------------------------
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
ORDER BY category, order_year;;

-- ----------------------------------------------------------
-- Q13_retained_customers
-- ----------------------------------------------------------
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
LIMIT 15;;

-- ----------------------------------------------------------
-- Q14_first_vs_latest
-- ----------------------------------------------------------
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
LIMIT 15;;

-- ----------------------------------------------------------
-- Q15_quarterly_pivot
-- ----------------------------------------------------------
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
ORDER BY order_year, annual_total DESC;;

