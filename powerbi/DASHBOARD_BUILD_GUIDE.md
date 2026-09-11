# Power BI Dashboard — Build Guide

**Smart Sales Intelligence Dashboard**
Author: Manya Kumar

This guide walks you through building a professional 4-page Power BI dashboard.
Follow it step by step. Estimated time: **45–60 minutes**.

---

## Prerequisites

1. Install **Power BI Desktop** (free): https://powerbi.microsoft.com/desktop/
2. Run the data prep script first (already done if you ran the project):
   ```
   python powerbi/prepare_powerbi_data.py
   ```
   This creates the star-schema CSVs in `powerbi/data_model/`.

---

## Step 1 — Import Data (5 min)

**Option A — Star Schema (recommended, looks professional):**

1. Open Power BI Desktop
2. Home → **Get Data** → **Text/CSV**
3. Import all 5 files from `powerbi/data_model/`:
   - `fact_sales.csv`
   - `dim_customer.csv`
   - `dim_product.csv`
   - `dim_geography.csv`
   - `dim_date.csv`
4. Click **Load** for each

**Option B — Quick Start (single file):**
- Just import `flat_sales.csv` and skip Step 2

---

## Step 2 — Build the Data Model (5 min)

1. Go to **Model view** (left sidebar, third icon)
2. Create these relationships by dragging fields:

   | From (fact_sales) | To (dimension)          | Cardinality |
   |-------------------|-------------------------|-------------|
   | customer_id       | dim_customer[customer_id] | Many-to-One |
   | product_id        | dim_product[product_id]   | Many-to-One |
   | geo_id            | dim_geography[geo_id]     | Many-to-One |
   | date_key          | dim_date[date_key]        | Many-to-One |

3. Click on **dim_date** table → Table tools → **Mark as Date Table** → select `date` column
   (This enables time-intelligence DAX measures)

---

## Step 3 — Add DAX Measures (10 min)

1. In Report view, Home → **Enter Data** → create empty table named `_Measures` → Load
2. Open `powerbi/DAX_measures.txt`
3. For each measure: right-click `_Measures` → **New Measure** → paste → Enter
4. Start with the **CORE MEASURES** section — those are used everywhere

At minimum add these to get started:
- Total Revenue, Total Profit, Total Orders, Profit Margin %, Avg Order Value
- Revenue YoY Growth %, Revenue MoM Growth %

---

## Step 4 — Set a Theme (2 min)

View → **Themes** → dropdown → **Browse for themes** → select `powerbi/theme.json`

This applies the blue/green corporate color palette matching the Python charts.

---

## PAGE 1 — Executive Overview

**Layout:** KPI cards on top, trend + category below.

### Top row — 4 KPI Cards
Insert → **Card** visual × 4:
| Card | Field |
|------|-------|
| Card 1 | `Total Revenue` (format as Cr) |
| Card 2 | `Total Profit` |
| Card 3 | `Profit Margin %` (format %) |
| Card 4 | `Total Orders` |

Style: white background, colored top border, large font.

### Middle — Revenue Trend (Line Chart)
- Visual: **Line chart**
- X-axis: `dim_date[year_month]`
- Y-axis: `Total Revenue`
- Title: "Monthly Revenue Trend"

### Bottom-left — Revenue by Category (Bar Chart)
- Visual: **Clustered bar chart**
- Y-axis: `dim_product[category]`
- X-axis: `Total Revenue`
- Sort descending

### Bottom-right — Revenue by Region (Donut Chart)
- Visual: **Donut chart**
- Legend: `dim_geography[region]`
- Values: `Total Revenue`

### Add a Slicer
- Visual: **Slicer** → Field: `dim_date[year]`
- Format as dropdown or tiles at top-right

---

## PAGE 2 — Regional & Geographic Analysis

### Map Visual
- Visual: **Map** (or Filled Map)
- Location: `dim_geography[city]`
- Bubble size: `Total Revenue`
- Legend: `dim_geography[region]`

### Region Comparison (Clustered Column)
- X-axis: `dim_geography[region]`
- Y-axis: `Total Revenue` and `Total Profit` (two series)

### Region Scorecard (Table/Matrix)
- Visual: **Matrix**
- Rows: `region`
- Values: `Total Revenue`, `Total Profit`, `Profit Margin %`, `Avg Order Value`, `Region Rank by Revenue`

### AOV by Region (Bar)
- Y-axis: `region`, X-axis: `Avg Order Value`

---

## PAGE 3 — Product & Category Deep Dive

### Top 10 Products (Bar Chart)
- Y-axis: `dim_product[product_name]`
- X-axis: `Total Revenue`
- Filter: Top N = 10 by Total Revenue (use visual-level filter)

### Category Treemap
- Visual: **Treemap**
- Group: `category`
- Values: `Total Revenue`

### Profit Margin by Category (Bar)
- Y-axis: `category`, X-axis: `Profit Margin %`
- Add data labels

### Product Table
- Visual: **Table**
- Columns: `product_name`, `category`, `Total Revenue`, `Total Profit`, `Profit Margin %`, `Product Rank`

---

## PAGE 4 — Customer & Discount Analysis

### Customer Segment Breakdown (Donut)
- Legend: `dim_customer[segment]`
- Values: `Total Revenue`

### Top 15 Customers (Bar Chart)
- Y-axis: `dim_customer[customer_name]`
- X-axis: `Total Revenue`
- Visual filter: Top 15

### Discount Impact (Combo Chart)
- Visual: **Line and clustered column chart**
- X-axis: `Discount Band` (calculated column)
- Column: `Total Orders`
- Line: `Profit Margin %`
- This visually shows margins dropping as discounts rise

### Customer Tier Matrix
- Rows: `customer_tier`
- Values: `Total Customers`, `Total Revenue`, `Avg Order Value`

---

## Step 5 — Polish (10 min)

1. **Consistent titles** on every visual
2. **Add slicers** on each page: Year, Region, Category
3. **Sync slicers** across pages: View → Sync Slicers
4. Add a **title text box** on each page header
5. Add your name in a footer text box
6. Enable **drill-through** from category to product (optional but impressive)

---

## Step 6 — Publish & Share (5 min)

1. Sign in with a Microsoft account (free Power BI account)
2. Home → **Publish** → select "My workspace"
3. In Power BI Service, open the report → File → **Publish to web** (public)
4. Copy the shareable link
5. **Add the link to your resume and GitHub README**

---

## Talking Points for Interviews

When asked about this dashboard, mention:

- **"I built a star schema data model"** — shows you understand dimensional modeling
- **"I used DAX time-intelligence functions"** — YoY and MoM growth measures
- **"I marked a proper date table"** — needed for time intelligence
- **"The discount combo chart revealed that margins drop from ~40% to ~14% as discounts increase past 30%"** — a real insight
- **"Q4 consistently drives ~29% of annual revenue"** — seasonality insight

---

## Screenshot Checklist for GitHub

Take screenshots of all 4 pages and add them to `powerbi/screenshots/`.
Reference them in your README so recruiters can see the dashboard without opening Power BI.
