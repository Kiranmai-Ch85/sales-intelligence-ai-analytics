"""
AI Sales Analytics Agent
=========================
Smart Sales Intelligence Dashboard
Author: Manya Kumar

A natural language query agent for the sales dataset.
Works completely offline - no API key required.

Understands questions like:
  - "Which region has the highest profit margin?"
  - "Show top 5 customers by revenue"
  - "What is the best performing category?"
  - "How did sales trend month over month?"
  - "Which products are most profitable?"
  - "What is the impact of discounts on profit?"
  - "Compare 2022 and 2024 revenue"
  - "Which city has the most orders?"

Usage:
  python agent.py                    # interactive mode
  python agent.py --demo             # run demo questions
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import sys
import re
import warnings
warnings.filterwarnings('ignore')

# Ensure UTF-8 output so bar chars/rupee symbols render on any console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'cleaned_sales_data.csv')
DB_PATH   = os.path.join(BASE_DIR, 'data', 'sales.db')

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df  = pd.read_csv(DATA_PATH, parse_dates=['order_date', 'ship_date'])
try:
    conn = sqlite3.connect(DB_PATH)
except Exception:
    conn = None

# ── HELPER FORMATTERS ─────────────────────────────────────────────────────────
def fmt_inr(val):
    if val >= 1e7:  return f"Rs.{val/1e7:.2f} Cr"
    if val >= 1e5:  return f"Rs.{val/1e5:.1f} L"
    if val >= 1e3:  return f"Rs.{val/1e3:.1f}K"
    return f"Rs.{val:.0f}"

def fmt_pct(val):
    return f"{val:.1f}%"

def divider():
    print("-" * 60)

def header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

# ── INTENT CLASSIFIER ─────────────────────────────────────────────────────────
INTENTS = {
    # Revenue / Sales
    "revenue_by_region":    ["revenue by region","sales by region","region revenue","region sales","which region"],
    "revenue_by_category":  ["revenue by category","category revenue","category sales","sales by category","best category","top category"],
    "revenue_trend":        ["revenue trend","monthly revenue","monthly sales","trend","month over month","mom"],
    "total_revenue":        ["total revenue","total sales","overall revenue","overall sales","how much revenue","how much sales"],

    # Profit
    "profit_by_category":   ["profit by category","most profitable category","category profit","profit margin category"],
    "profit_by_region":     ["profit by region","region profit","profit margin region","most profitable region"],
    "profit_overall":       ["total profit","overall profit","how much profit","net profit"],

    # Customers
    "top_customers":        ["top customer","best customer","highest revenue customer","most valuable customer","top 5 customer","top 10 customer"],
    "customer_segments":    ["segment","consumer","corporate","home office","customer segment"],
    "customer_retention":   ["retained","returning","loyal","repeat customer","comeback"],

    # Products
    "top_products":         ["top product","best product","best selling","most sold","highest selling","popular product"],
    "bottom_products":      ["bottom product","least profitable","worst product","loss making","losing money"],
    "product_margin":       ["product margin","most profitable product","highest margin product"],

    # Discounts
    "discount_impact":      ["discount","discount impact","high discount","low discount","discount band","discount effect"],

    # Time / Year
    "yearly_comparison":    ["compare year","year comparison","2021","2022","2023","2024","annual","yoy","year over year"],
    "quarterly":            ["quarter","q1","q2","q3","q4","quarterly"],

    # Geography
    "city_analysis":        ["city","cities","which city","top city","best city"],
    "region_scorecard":     ["region scorecard","region performance","region comparison","compare region"],

    # Shipping
    "shipping":             ["ship","shipping","delivery","days to ship","ship mode","fastest","slowest"],

    # Summary
    "summary":              ["summary","overview","dashboard","kpi","key metrics","tell me about","describe","what can you"],

    # Help
    "help":                 ["help","what can","what do you","questions","capabilities","how to use"],
}

def classify_intent(question):
    q = question.lower()
    scores = {}
    for intent, keywords in INTENTS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[intent] = score
    if not scores:
        return "unknown"
    return max(scores, key=scores.get)

# ── RESPONSE HANDLERS ─────────────────────────────────────────────────────────

def handle_revenue_by_region(q):
    result = df.groupby('region').agg(
        total_revenue=('sales','sum'),
        total_orders=('order_id','count'),
        avg_order_value=('sales','mean')
    ).sort_values('total_revenue', ascending=False).reset_index()

    header("Revenue by Region")
    for _, row in result.iterrows():
        bar = "█" * int(row['total_revenue'] / result['total_revenue'].max() * 20)
        print(f"  {row['region']:<10} {bar:<22} {fmt_inr(row['total_revenue'])}  "
              f"({row['total_orders']} orders, AOV: {fmt_inr(row['avg_order_value'])})")

    best = result.iloc[0]
    worst = result.iloc[-1]
    divider()
    print(f"  INSIGHT: {best['region']} leads with {fmt_inr(best['total_revenue'])} revenue.")
    print(f"  {worst['region']} has the lowest at {fmt_inr(worst['total_revenue'])}.")
    print(f"  Gap between best and worst: {fmt_inr(best['total_revenue'] - worst['total_revenue'])}")

def handle_revenue_by_category(q):
    result = df.groupby('category').agg(
        total_revenue=('sales','sum'),
        total_profit=('profit','sum'),
        orders=('order_id','count')
    ).sort_values('total_revenue', ascending=False).reset_index()
    result['margin'] = (result['total_profit'] / result['total_revenue'] * 100).round(1)
    result['share']  = (result['total_revenue'] / result['total_revenue'].sum() * 100).round(1)

    header("Revenue by Category")
    print(f"  {'Category':<22} {'Revenue':>12} {'Share':>7} {'Margin':>8} {'Orders':>7}")
    divider()
    for _, row in result.iterrows():
        print(f"  {row['category']:<22} {fmt_inr(row['total_revenue']):>12} "
              f"{row['share']:>6.1f}%  {row['margin']:>6.1f}%  {row['orders']:>7,}")
    divider()
    top = result.iloc[0]
    print(f"  INSIGHT: {top['category']} dominates at {top['share']}% of revenue")
    print(f"  but has the lowest margin ({result.loc[result['margin'].idxmin(),'category']} "
          f"has lowest at {result['margin'].min()}%)")

def handle_total_revenue(q):
    total_rev    = df['sales'].sum()
    total_profit = df['profit'].sum()
    margin       = total_profit / total_rev * 100
    orders       = len(df)
    customers    = df['customer_id'].nunique()
    aov          = total_rev / orders

    header("Overall Revenue Summary")
    print(f"  Total Revenue  : {fmt_inr(total_rev)}")
    print(f"  Total Profit   : {fmt_inr(total_profit)}")
    print(f"  Profit Margin  : {fmt_pct(margin)}")
    print(f"  Total Orders   : {orders:,}")
    print(f"  Unique Customers: {customers:,}")
    print(f"  Avg Order Value : {fmt_inr(aov)}")
    print(f"  Period         : {df['order_date'].min().date()} to {df['order_date'].max().date()}")

def handle_profit_by_category(q):
    result = df.groupby('category').agg(
        total_profit=('profit','sum'),
        total_revenue=('sales','sum')
    ).reset_index()
    result['margin'] = (result['total_profit'] / result['total_revenue'] * 100).round(1)
    result = result.sort_values('margin', ascending=False)

    header("Profit Margin by Category")
    print(f"  {'Category':<22} {'Total Profit':>14} {'Margin':>8}")
    divider()
    for _, row in result.iterrows():
        bar = "█" * int(row['margin'] / result['margin'].max() * 15)
        print(f"  {row['category']:<22} {fmt_inr(row['total_profit']):>14}  "
              f"{fmt_pct(row['margin']):>7}  {bar}")
    divider()
    best = result.iloc[0]
    print(f"  INSIGHT: {best['category']} has the best margin at {fmt_pct(best['margin'])}")

def handle_profit_by_region(q):
    result = df.groupby('region').agg(
        total_profit=('profit','sum'),
        total_revenue=('sales','sum')
    ).reset_index()
    result['margin'] = (result['total_profit'] / result['total_revenue'] * 100).round(1)
    result = result.sort_values('margin', ascending=False)

    header("Profit Margin by Region")
    for _, row in result.iterrows():
        bar = "█" * int(row['margin'] / result['margin'].max() * 20)
        print(f"  {row['region']:<10} {bar:<22} {fmt_pct(row['margin'])}  "
              f"(Profit: {fmt_inr(row['total_profit'])})")
    divider()
    print(f"  INSIGHT: {result.iloc[0]['region']} has the highest margin at "
          f"{fmt_pct(result.iloc[0]['margin'])}")

def handle_total_profit(q):
    total_profit = df['profit'].sum()
    margin       = total_profit / df['sales'].sum() * 100
    header("Overall Profit Summary")
    print(f"  Total Profit  : {fmt_inr(total_profit)}")
    print(f"  Profit Margin : {fmt_pct(margin)}")
    print(f"  Best Year     : {df.groupby('order_year')['profit'].sum().idxmax()}")

def handle_top_customers(q):
    # Extract number if mentioned
    n = 10
    match = re.search(r'top\s+(\d+)', q.lower())
    if match:
        n = int(match.group(1))

    result = df.groupby(['customer_name','region','segment']).agg(
        total_revenue=('sales','sum'),
        total_profit=('profit','sum'),
        orders=('order_id','count')
    ).reset_index().sort_values('total_revenue', ascending=False).head(n)

    header(f"Top {n} Customers by Revenue")
    print(f"  {'#':<4} {'Customer':<22} {'Region':<8} {'Segment':<12} {'Revenue':>12} {'Orders':>7}")
    divider()
    for i, (_, row) in enumerate(result.iterrows(), 1):
        print(f"  {i:<4} {row['customer_name']:<22} {row['region']:<8} "
              f"{row['segment']:<12} {fmt_inr(row['total_revenue']):>12} {row['orders']:>7}")
    divider()
    top = result.iloc[0]
    print(f"  INSIGHT: {top['customer_name']} is the top customer with "
          f"{fmt_inr(top['total_revenue'])} revenue across {top['orders']} orders.")

def handle_customer_segments(q):
    result = df.groupby('segment').agg(
        revenue=('sales','sum'),
        profit=('profit','sum'),
        orders=('order_id','count'),
        customers=('customer_id','nunique')
    ).reset_index()
    result['margin']       = (result['profit'] / result['revenue'] * 100).round(1)
    result['aov']          = (result['revenue'] / result['orders']).round(0)
    result['orders_per_c'] = (result['orders'] / result['customers']).round(1)

    header("Customer Segment Analysis")
    for _, row in result.iterrows():
        print(f"\n  [{row['segment']}]")
        print(f"    Revenue      : {fmt_inr(row['revenue'])}")
        print(f"    Profit Margin: {fmt_pct(row['margin'])}")
        print(f"    Orders       : {row['orders']:,}  (Avg: {row['orders_per_c']} per customer)")
        print(f"    Avg Order Val: {fmt_inr(row['aov'])}")
        print(f"    Customers    : {row['customers']}")

def handle_top_products(q):
    n = 10
    match = re.search(r'top\s+(\d+)', q.lower())
    if match:
        n = int(match.group(1))

    result = df.groupby(['product_name','category']).agg(
        total_sales=('sales','sum'),
        total_profit=('profit','sum'),
        orders=('order_id','count'),
        avg_margin=('profit_margin','mean')
    ).reset_index().sort_values('total_sales', ascending=False).head(n)

    header(f"Top {n} Products by Revenue")
    print(f"  {'#':<4} {'Product':<30} {'Category':<20} {'Revenue':>12} {'Margin':>8}")
    divider()
    for i, (_, row) in enumerate(result.iterrows(), 1):
        print(f"  {i:<4} {row['product_name']:<30} {row['category']:<20} "
              f"{fmt_inr(row['total_sales']):>12} {fmt_pct(row['avg_margin']):>8}")

def handle_bottom_products(q):
    result = df.groupby(['product_name','category']).agg(
        total_profit=('profit','sum'),
        total_sales=('sales','sum'),
        orders=('order_id','count')
    ).reset_index().sort_values('total_profit').head(10)

    header("Bottom 10 Products by Profit")
    print(f"  {'Product':<30} {'Category':<20} {'Profit':>14} {'Revenue':>12}")
    divider()
    for _, row in result.iterrows():
        flag = "  [LOSS]" if row['total_profit'] < 0 else ""
        print(f"  {row['product_name']:<30} {row['category']:<20} "
              f"{fmt_inr(row['total_profit']):>14} {fmt_inr(row['total_sales']):>12}{flag}")

def handle_discount_impact(q):
    disc_order = ['No Discount','Low (1-10%)','Medium (11-20%)','High (21-30%)','Very High (>30%)']
    result = df.groupby('discount_band', observed=True).agg(
        orders=('order_id','count'),
        avg_margin=('profit_margin','mean'),
        avg_profit=('profit','mean'),
        total_revenue=('sales','sum')
    ).reset_index()
    result['discount_band'] = pd.Categorical(result['discount_band'],
                                              categories=disc_order, ordered=True)
    result = result.sort_values('discount_band')

    header("Discount Impact on Profitability")
    print(f"  {'Discount Band':<22} {'Orders':>7} {'Avg Margin':>11} {'Avg Profit':>12}")
    divider()
    for _, row in result.iterrows():
        bar = "█" * max(1, int(row['avg_margin'] / 45 * 15))
        print(f"  {str(row['discount_band']):<22} {row['orders']:>7,} "
              f"{fmt_pct(row['avg_margin']):>11}  {fmt_inr(row['avg_profit']):>12}  {bar}")
    divider()
    no_disc = result[result['discount_band']=='No Discount']['avg_margin'].values[0]
    hi_disc = result[result['discount_band']=='Very High (>30%)']['avg_margin'].values
    if len(hi_disc):
        drop = no_disc - hi_disc[0]
        print(f"  INSIGHT: Very High discounts reduce margin by {fmt_pct(drop)} vs No Discount")
    print(f"  RECOMMENDATION: Cap discounts at 20% to protect margins.")

def handle_revenue_trend(q):
    result = df.groupby(['order_year','order_month']).agg(
        revenue=('sales','sum')
    ).reset_index().sort_values(['order_year','order_month'])

    # Show yearly summary with monthly breakdown
    header("Monthly Revenue Trend")
    for year in sorted(result['order_year'].unique()):
        yr_data = result[result['order_year']==year]
        yr_total = yr_data['revenue'].sum()
        print(f"\n  {year}  (Total: {fmt_inr(yr_total)})")
        for _, row in yr_data.iterrows():
            bar_len = int(row['revenue'] / result['revenue'].max() * 25)
            bar = "█" * bar_len
            month_name = ['Jan','Feb','Mar','Apr','May','Jun',
                          'Jul','Aug','Sep','Oct','Nov','Dec'][int(row['order_month'])-1]
            print(f"    {month_name}  {bar:<27} {fmt_inr(row['revenue'])}")

    divider()
    # YoY growth
    yearly = df.groupby('order_year')['sales'].sum()
    print(f"\n  Year-over-Year Growth:")
    years = sorted(yearly.index)
    for i in range(1, len(years)):
        growth = (yearly[years[i]] - yearly[years[i-1]]) / yearly[years[i-1]] * 100
        arrow = "+" if growth >= 0 else ""
        print(f"    {years[i-1]} -> {years[i]}: {arrow}{growth:.1f}%")

def handle_yearly_comparison(q):
    # Extract years from question
    years_mentioned = re.findall(r'20\d\d', q)

    yearly = df.groupby('order_year').agg(
        revenue=('sales','sum'),
        profit=('profit','sum'),
        orders=('order_id','count')
    ).reset_index()
    yearly['margin'] = (yearly['profit'] / yearly['revenue'] * 100).round(1)

    header("Year-by-Year Performance Comparison")
    print(f"  {'Year':<8} {'Revenue':>14} {'Profit':>12} {'Margin':>8} {'Orders':>8}")
    divider()
    for _, row in yearly.iterrows():
        print(f"  {int(row['order_year']):<8} {fmt_inr(row['revenue']):>14} "
              f"{fmt_inr(row['profit']):>12} {fmt_pct(row['margin']):>8} {int(row['orders']):>8,}")
    divider()
    best_year = yearly.loc[yearly['revenue'].idxmax(), 'order_year']
    print(f"  INSIGHT: {int(best_year)} was the best revenue year.")
    if years_mentioned and len(years_mentioned) >= 2:
        y1, y2 = int(years_mentioned[0]), int(years_mentioned[1])
        r1 = yearly[yearly['order_year']==y1]['revenue'].values
        r2 = yearly[yearly['order_year']==y2]['revenue'].values
        if len(r1) and len(r2):
            diff = (r2[0] - r1[0]) / r1[0] * 100
            print(f"  {y1} vs {y2}: {'+' if diff>=0 else ''}{diff:.1f}% change in revenue")

def handle_quarterly(q):
    result = df.groupby(['order_year','order_quarter']).agg(
        revenue=('sales','sum')
    ).reset_index()
    pivot = result.pivot(index='order_year', columns='order_quarter', values='revenue').fillna(0)
    pivot.columns = [f'Q{c}' for c in pivot.columns]

    header("Quarterly Revenue Breakdown")
    print(f"  {'Year':<8}", end="")
    for col in pivot.columns:
        print(f" {col:>14}", end="")
    print(f"  {'Q4 vs Q1':>10}")
    divider()
    for year, row in pivot.iterrows():
        print(f"  {int(year):<8}", end="")
        for col in pivot.columns:
            print(f" {fmt_inr(row[col]):>14}", end="")
        if row['Q1'] > 0:
            growth = (row['Q4'] - row['Q1']) / row['Q1'] * 100
            print(f"  {'+' if growth>=0 else ''}{growth:.1f}%")
        else:
            print()
    divider()
    q4_avg = result[result['order_quarter']==4]['revenue'].mean()
    q1_avg = result[result['order_quarter']==1]['revenue'].mean()
    print(f"  INSIGHT: Q4 averages {fmt_inr(q4_avg)} vs Q1 at {fmt_inr(q1_avg)} "
          f"({(q4_avg-q1_avg)/q1_avg*100:.0f}% higher).")

def handle_city_analysis(q):
    result = df.groupby(['city','region']).agg(
        revenue=('sales','sum'),
        orders=('order_id','count'),
        customers=('customer_id','nunique')
    ).reset_index().sort_values('revenue', ascending=False).head(15)

    header("Top 15 Cities by Revenue")
    print(f"  {'#':<4} {'City':<16} {'Region':<10} {'Revenue':>12} {'Orders':>8} {'Customers':>10}")
    divider()
    for i, (_, row) in enumerate(result.iterrows(), 1):
        print(f"  {i:<4} {row['city']:<16} {row['region']:<10} "
              f"{fmt_inr(row['revenue']):>12} {row['orders']:>8,} {row['customers']:>10}")

def handle_region_scorecard(q):
    result = df.groupby('region').agg(
        revenue=('sales','sum'),
        profit=('profit','sum'),
        orders=('order_id','count'),
        customers=('customer_id','nunique'),
        aov=('sales','mean')
    ).reset_index()
    result['margin']  = (result['profit'] / result['revenue'] * 100).round(1)
    result['rev_rank'] = result['revenue'].rank(ascending=False).astype(int)
    result['mgn_rank'] = result['margin'].rank(ascending=False).astype(int)
    result = result.sort_values('revenue', ascending=False)

    header("Regional Performance Scorecard")
    for _, row in result.iterrows():
        print(f"\n  [{row['region']}]  Revenue Rank: #{row['rev_rank']}  |  Margin Rank: #{row['mgn_rank']}")
        print(f"    Revenue         : {fmt_inr(row['revenue'])}")
        print(f"    Profit          : {fmt_inr(row['profit'])}  ({fmt_pct(row['margin'])})")
        print(f"    Orders          : {row['orders']:,}")
        print(f"    Customers       : {row['customers']}")
        print(f"    Avg Order Value : {fmt_inr(row['aov'])}")

def handle_shipping(q):
    result = df.groupby('ship_mode').agg(
        orders=('order_id','count'),
        avg_days=('days_to_ship','mean'),
        revenue=('sales','sum')
    ).reset_index().sort_values('orders', ascending=False)
    result['share'] = (result['orders'] / result['orders'].sum() * 100).round(1)

    header("Shipping Analysis")
    print(f"  {'Ship Mode':<18} {'Orders':>8} {'Share':>7} {'Avg Days':>10} {'Revenue':>14}")
    divider()
    for _, row in result.iterrows():
        print(f"  {row['ship_mode']:<18} {row['orders']:>8,} {row['share']:>6.1f}%"
              f"  {row['avg_days']:>8.1f}d  {fmt_inr(row['revenue']):>14}")
    divider()
    fastest = result.loc[result['avg_days'].idxmin(), 'ship_mode']
    most_used = result.iloc[0]['ship_mode']
    print(f"  Most used  : {most_used} ({result.iloc[0]['share']}% of orders)")
    print(f"  Fastest    : {fastest}")

def handle_summary(q):
    total_rev    = df['sales'].sum()
    total_profit = df['profit'].sum()
    margin       = total_profit / total_rev * 100
    best_region  = df.groupby('region')['sales'].sum().idxmax()
    best_cat     = df.groupby('category')['sales'].sum().idxmax()
    best_year    = df.groupby('order_year')['sales'].sum().idxmax()
    top_cust     = df.groupby('customer_name')['sales'].sum().idxmax()

    header("Executive Dashboard Summary")
    print(f"""
  FINANCIAL OVERVIEW
  ------------------
  Total Revenue      : {fmt_inr(total_rev)}
  Total Profit       : {fmt_inr(total_profit)}
  Overall Margin     : {fmt_pct(margin)}
  Total Orders       : {len(df):,}
  Unique Customers   : {df['customer_id'].nunique():,}
  Products           : {df['product_name'].nunique():,} SKUs

  TOP PERFORMERS
  --------------
  Best Region        : {best_region}
  Best Category      : {best_cat}
  Best Year          : {int(best_year)}
  Top Customer       : {top_cust}

  KEY INSIGHTS
  ------------
  1. Electronics = {df[df['category']=='Electronics']['sales'].sum()/total_rev*100:.0f}% revenue,
     lowest margin at {df[df['category']=='Electronics']['profit_margin'].mean():.1f}%
  2. Q4 = {df[df['order_quarter']==4]['sales'].sum()/total_rev*100:.0f}% of annual revenue (festive season)
  3. No-discount orders have {df[df['discount']==0]['profit_margin'].mean():.1f}% avg margin vs
     {df[df['discount']>0.3]['profit_margin'].mean():.1f}% for >30% discount orders
  4. West region leads profit margin at
     {df.groupby('region')['profit_margin'].mean()['West']:.1f}%
  5. Top 20 customers = {df.groupby('customer_name')['sales'].sum().nlargest(20).sum()/total_rev*100:.0f}% of revenue
    """)

def handle_help(q):
    header("What can I answer?")
    print("""
  REVENUE QUESTIONS
    "What is the total revenue?"
    "Show revenue by region"
    "Revenue by category"
    "Monthly revenue trend"

  PROFIT QUESTIONS
    "Which category is most profitable?"
    "Profit margin by region"
    "Total profit for 2023"

  CUSTOMER QUESTIONS
    "Show top 10 customers"
    "How do customer segments compare?"

  PRODUCT QUESTIONS
    "Which are the best selling products?"
    "Show bottom 10 products by profit"
    "Most profitable products"

  DISCOUNT ANALYSIS
    "How do discounts impact profit?"
    "Show discount band analysis"

  TIME ANALYSIS
    "Compare 2022 and 2024 revenue"
    "Show quarterly breakdown"
    "Year over year growth"

  GEOGRAPHY
    "Top cities by revenue"
    "Regional scorecard"

  SHIPPING
    "Shipping mode analysis"

  GENERAL
    "Give me a summary"
    "Show executive dashboard"
    """)

def handle_unknown(q):
    header("Could not understand the question")
    print(f"  Question: '{q}'")
    print("\n  Try rephrasing, or type 'help' to see what I can answer.")
    print("  Examples:")
    print("    'Which region has the most revenue?'")
    print("    'Show top 5 customers'")
    print("    'What is the profit margin by category?'")

# ── DISPATCH TABLE ────────────────────────────────────────────────────────────
HANDLERS = {
    "revenue_by_region":   handle_revenue_by_region,
    "revenue_by_category": handle_revenue_by_category,
    "total_revenue":       handle_total_revenue,
    "revenue_trend":       handle_revenue_trend,
    "profit_by_category":  handle_profit_by_category,
    "profit_by_region":    handle_profit_by_region,
    "profit_overall":      handle_total_profit,
    "top_customers":       handle_top_customers,
    "customer_segments":   handle_customer_segments,
    "customer_retention":  handle_customer_segments,
    "top_products":        handle_top_products,
    "bottom_products":     handle_bottom_products,
    "product_margin":      handle_top_products,
    "discount_impact":     handle_discount_impact,
    "yearly_comparison":   handle_yearly_comparison,
    "quarterly":           handle_quarterly,
    "city_analysis":       handle_city_analysis,
    "region_scorecard":    handle_region_scorecard,
    "shipping":            handle_shipping,
    "summary":             handle_summary,
    "help":                handle_help,
    "unknown":             handle_unknown,
}

def answer(question):
    intent = classify_intent(question)
    handler = HANDLERS.get(intent, handle_unknown)
    handler(question)
    print()

# ── DEMO MODE ─────────────────────────────────────────────────────────────────
DEMO_QUESTIONS = [
    "Give me a summary of the business",
    "Which region has the highest revenue?",
    "Show the top 5 customers by revenue",
    "What is the best performing category by profit margin?",
    "How do discounts impact profit margin?",
    "Show revenue trend month over month",
    "Compare 2021 and 2024 revenue",
    "Which are the top 10 products?",
    "Show quarterly breakdown",
    "Shipping mode analysis",
]

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    demo_mode = "--demo" in sys.argv

    print("\n" + "=" * 60)
    print("  SMART SALES AI AGENT")
    print("  Ask questions about your sales data in plain English")
    print("  Type 'help' to see what I can answer")
    print("  Type 'exit' or 'quit' to stop")
    print("=" * 60)
    print(f"\n  Dataset: {len(df):,} orders | "
          f"{df['order_date'].min().year}-{df['order_date'].max().year} | "
          f"Total Revenue: {fmt_inr(df['sales'].sum())}\n")

    if demo_mode:
        print("[DEMO MODE] Running sample questions...\n")
        for q in DEMO_QUESTIONS:
            print(f"\n  QUESTION: {q}")
            answer(q)
            input("  Press Enter for next question...")
        return

    while True:
        try:
            user_input = input("\n  Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
            print("  Goodbye!")
            break

        answer(user_input)


if __name__ == "__main__":
    main()
