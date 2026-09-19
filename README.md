# Sales Intelligence & AI-Assisted Business Analytics

**End-to-end business analytics project** — Python, SQL, Power BI, and a basic natural-language query agent, extended with foundational AI/ML, Generative AI, and prompt engineering concepts.

> A practical analytics project covering data preparation, exploratory analysis, SQL business queries, Power BI dashboarding, and beginner-level AI-assisted analysis.
---

## Business Problem

A mid-sized retail company wants to understand **what drives its revenue and profit** across categories, regions, customers, and time — and identify where margins are leaking. This project turns raw transaction data into actionable business intelligence.

**Key questions answered:**
- Which categories and regions drive revenue vs profit?
- How do discounts affect profit margins?
- Who are the most valuable customers?
- What are the seasonal and year-over-year trends?
- Which products are profitable vs loss-making?

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data Processing | Python, Pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Database & Analysis | SQL (SQLite), Window functions, CTEs |
| Business Intelligence | Power BI (star schema, DAX) |
| AI Agent | Python (rule-based NLP, no API key needed) |
| Data Source | Excel / CSV |

---

## Project Structure

```
sales_analytics_project/
├── data/
│   ├── generate_dataset.py          # synthetic dataset generator
│   ├── raw_sales_data.csv           # 5,000 raw records
│   ├── cleaned_sales_data.csv       # cleaned + 29 engineered features
│   └── sales.db                     # SQLite database
├── python/
│   ├── 01_data_cleaning.py          # audit, clean, feature engineering
│   ├── 02_eda.py                    # 12 visualizations + insights
│   └── 03_sql_analysis.py           # loads DB + runs 15 SQL queries
├── sql/
│   └── analysis_queries.sql         # 15 documented business queries
├── ai_agent/
│   └── agent.py                     # natural-language data query agent
├── powerbi/
│   ├── prepare_powerbi_data.py      # builds star-schema tables
│   ├── data_model/                  # fact + dimension CSVs
│   ├── DAX_measures.txt             # 30+ ready-to-paste DAX measures
│   ├── DASHBOARD_BUILD_GUIDE.md     # step-by-step dashboard guide
│   └── theme.json                   # Power BI color theme
├── outputs/
│   ├── plots/                       # 12 PNG visualizations
│   └── reports/                     # insights + SQL results + quality report
└── README.md
```

---

## How to Run

```bash
# 1. Generate the dataset
python data/generate_dataset.py

# 2. Clean and engineer features
python python/01_data_cleaning.py

# 3. Run EDA and generate all visualizations
python python/02_eda.py

# 4. Load into SQL and run 15 business queries
python python/03_sql_analysis.py

# 5. Prepare Power BI star-schema data
python powerbi/prepare_powerbi_data.py

# 6. Launch the AI agent (interactive)
python ai_agent/agent.py
```

**Requirements:** `pip install pandas numpy matplotlib seaborn`

---

## Dataset Overview

- **5,000** order records | **2021–2024** (4 years)
- **300** unique customers | **50** products | **5** categories
- **4** regions, **20** cities
- **₹6.48 Cr** total revenue | **₹1.39 Cr** total profit

**Engineered features:** date parts, days-to-ship, discount bands, sales bands, customer LTV, customer tier, revenue share, profitability flag.

---

## Key Insights

### 1. Electronics drives volume, not margin
Electronics contributes **~78% of revenue** but has the **lowest profit margin (~18%)**. High price points drive sales, but discount pressure compresses profitability.
→ *Recommendation: Reduce discounting on high-value electronics.*

### 2. Discounts sharply erode margins
No-discount orders average **~40% margin**; orders with >30% discount collapse to **~14%**.
→ *Recommendation: Cap discounts at 20% except for clearance.*

### 3. Q4 seasonality is significant
Q4 (Oct–Dec) consistently contributes **~29% of annual revenue**, driven by festive demand.
→ *Recommendation: Increase inventory and marketing spend in Sept–Oct.*

### 4. West region leads profitability
West achieves the **highest profit margin (~23% effective / 35% avg)** despite not being the top revenue region — premium product mix, lower discount demand.
→ *Recommendation: Replicate West's playbook in lower-margin regions.*

### 5. Pareto principle in customers
The **top 20 customers** drive a disproportionate share of revenue.
→ *Recommendation: Launch a tiered loyalty program.*

Full insights: [`outputs/reports/key_insights.txt`](outputs/reports/key_insights.txt)

---

## SQL Analysis Highlights

15 documented queries in [`sql/analysis_queries.sql`](sql/analysis_queries.sql), covering:

- **Aggregations & HAVING** — category summaries, high-value customers
- **Window functions** — `RANK`, `DENSE_RANK`, `ROW_NUMBER`, `LAG`, `FIRST_VALUE`
- **CTEs** — single and chained (regional scorecard)
- **Subqueries** — correlated (customers vs segment average)
- **Running totals** — cumulative YTD revenue
- **CASE WHEN** — conditional aggregation / quarterly pivots
- **INTERSECT** — customer retention analysis
- **Date functions** — monthly/quarterly/yearly trends

Example — Month-over-Month growth with `LAG`:
```sql
WITH monthly AS (
    SELECT order_year, order_month, ROUND(SUM(sales),0) AS revenue
    FROM sales GROUP BY order_year, order_month
),
with_lag AS (
    SELECT *, LAG(revenue) OVER (ORDER BY order_year, order_month) AS prev_revenue
    FROM monthly
)
SELECT order_year, order_month, revenue, prev_revenue,
       ROUND((revenue - prev_revenue) * 100.0 / prev_revenue, 1) AS mom_growth_pct
FROM with_lag WHERE prev_revenue IS NOT NULL;
```

---

## Visualizations

12 publication-quality charts in [`outputs/plots/`](outputs/plots/):

| # | Chart | # | Chart |
|---|-------|---|-------|
| 01 | Monthly revenue trend | 07 | Shipping analysis |
| 02 | Category performance | 08 | Customer segments |
| 03 | Regional analysis | 09 | Quarterly heatmap |
| 04 | Discount impact | 10 | YoY growth by category |
| 05 | Top customers | 11 | Correlation matrix |
| 06 | Product profitability | 12 | Executive summary dashboard |

---

## AI Sales Agent

A natural-language query agent that answers business questions in plain English — **no API key or internet required** (rule-based intent classification).

```
Your question: which region has the highest profit margin?

============================================================
  Profit Margin by Region
============================================================
  West       ████████████████████ 35.1%  (Profit: Rs.50.3 L)
  South      ████████████████     32.8%  ...
  ...
```

**Supported questions:** revenue/profit by region or category, top customers/products, discount impact, quarterly/yearly comparisons, shipping analysis, executive summary, and more. Type `help` in the agent to see all.

```bash
python ai_agent/agent.py          # interactive
python ai_agent/agent.py --demo   # guided demo
```

---

## Power BI Dashboard

A 4-page interactive dashboard built on a **star-schema data model**:

1. **Executive Overview** — KPIs, revenue trend, category & region breakdown
2. **Regional Analysis** — map, region comparison, scorecard matrix
3. **Product Deep Dive** — top products, category treemap, margin analysis
4. **Customer & Discount** — segments, top customers, discount-vs-margin combo

The build package includes:
- Star-schema CSVs (`powerbi/data_model/`)
- 30+ DAX measures (`powerbi/DAX_measures.txt`) — including time-intelligence (YoY, MoM, YTD)
- Step-by-step build guide (`powerbi/DASHBOARD_BUILD_GUIDE.md`)
- Custom color theme (`powerbi/theme.json`)

> Note: `.pbix` files are built in Power BI Desktop. Follow the build guide (~45 min) then add screenshots to `powerbi/screenshots/`.

---

## Skills Demonstrated

- **Data cleaning & feature engineering** — data quality audits, derived features
- **Exploratory data analysis** — trend, distribution, correlation, segmentation
- **SQL proficiency** — window functions, CTEs, subqueries, conditional aggregation
- **Dimensional modeling** — star schema for BI
- **DAX & time intelligence** — YoY/MoM/YTD measures
- **Business storytelling** — translating data into recommendations
- **Automation** — reproducible end-to-end pipeline

---

## Author

**Manya Kumar**
B.Tech, IIT (ISM) Dhanbad | BS Data Science, IIT Madras

---

*This project uses a synthetically generated dataset with realistic business patterns (seasonality, regional variation, discount-margin dynamics) built specifically to demonstrate analytical techniques.*
