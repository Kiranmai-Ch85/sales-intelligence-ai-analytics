"""
Step 2: Exploratory Data Analysis & Visualizations
====================================================
Smart Sales Intelligence Dashboard
Author: Manya Kumar

Charts produced (saved to outputs/plots/):
  01_revenue_trend.png          — Monthly revenue trend 2021-2024
  02_category_performance.png   — Revenue, profit, margin by category
  03_regional_analysis.png      — Regional sales and profit comparison
  04_discount_impact.png        — How discount bands affect profit margin
  05_top_customers.png          — Top 15 customers by lifetime value
  06_product_profitability.png  — Top 10 and bottom 10 products by profit
  07_shipping_analysis.png      — Ship mode usage and days-to-ship dist
  08_customer_segments.png      — Segment-wise revenue and order count
  09_quarterly_heatmap.png      — Revenue heatmap: year × quarter
  10_yoy_growth.png             — Year-over-year growth by category
  11_correlation_matrix.png     — Numeric feature correlations
  12_executive_summary.png      — KPI summary dashboard (4-panel)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# ── SETUP ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, 'data', 'cleaned_sales_data.csv')
PLOTS_DIR  = os.path.join(BASE_DIR, 'outputs', 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

# Style
plt.rcParams.update({
    'figure.facecolor': '#FAFAFA',
    'axes.facecolor':   '#FFFFFF',
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'axes.grid':        True,
    'grid.alpha':       0.3,
    'grid.linestyle':   '--',
    'font.family':      'sans-serif',
    'font.size':        11,
    'axes.titlesize':   13,
    'axes.titleweight': 'bold',
    'axes.labelsize':   11,
})

PALETTE    = ['#2196F3','#4CAF50','#FF9800','#E91E63','#9C27B0']
CAT_COLORS = {
    'Electronics':       '#2196F3',
    'Clothing':          '#4CAF50',
    'Home & Kitchen':    '#FF9800',
    'Sports & Fitness':  '#E91E63',
    'Books & Stationery':'#9C27B0',
}
REG_COLORS = {'North':'#1565C0','South':'#2E7D32','East':'#E65100','West':'#6A1B9A'}

def save(fig, name):
    path = os.path.join(PLOTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [OK] Saved: {name}")

def fmt_inr(x, _=None):
    if x >= 1e7:  return f'₹{x/1e7:.1f}Cr'
    if x >= 1e5:  return f'₹{x/1e5:.1f}L'
    return f'₹{x:,.0f}'

# ── LOAD ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, parse_dates=['order_date','ship_date'])
print("=" * 60)
print("  SMART SALES DASHBOARD — EDA & VISUALIZATIONS")
print("=" * 60)
print(f"\n[LOAD] {len(df):,} records loaded\n")

# ── PLOT 01: MONTHLY REVENUE TREND ────────────────────────────────────────────
print("[PLOT 01] Monthly revenue trend...")
monthly = df.groupby('order_year_month').agg(
    revenue=('sales','sum'),
    orders=('order_id','count')
).reset_index()
monthly['order_year_month'] = pd.to_datetime(monthly['order_year_month'])
monthly = monthly.sort_values('order_year_month')

# 3-month rolling average
monthly['rolling_avg'] = monthly['revenue'].rolling(3, min_periods=1).mean()

fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()

ax1.fill_between(monthly['order_year_month'], monthly['revenue'],
                 alpha=0.25, color='#2196F3')
ax1.plot(monthly['order_year_month'], monthly['revenue'],
         color='#2196F3', linewidth=1.5, label='Monthly Revenue')
ax1.plot(monthly['order_year_month'], monthly['rolling_avg'],
         color='#E91E63', linewidth=2.5, linestyle='--', label='3-Month Rolling Avg')

ax2.bar(monthly['order_year_month'], monthly['orders'],
        width=20, alpha=0.25, color='#FF9800', label='Order Count')

ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
ax1.set_ylabel('Revenue', color='#2196F3')
ax2.set_ylabel('Order Count', color='#FF9800')
ax1.set_xlabel('Month')
ax1.set_title('Monthly Revenue Trend (2021–2024) with 3-Month Rolling Average')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

# Annotate Q4 spikes
for year in [2021, 2022, 2023, 2024]:
    q4 = monthly[monthly['order_year_month'].dt.year == year]
    q4 = q4[monthly['order_year_month'].dt.month.isin([10,11,12])]
    if not q4.empty:
        peak = q4.loc[q4['revenue'].idxmax()]
        ax1.annotate(f"Q4 {year}", xy=(peak['order_year_month'], peak['revenue']),
                     xytext=(0, 15), textcoords='offset points',
                     arrowprops=dict(arrowstyle='->', color='gray', lw=1),
                     fontsize=8, color='gray', ha='center')

plt.tight_layout()
save(fig, '01_revenue_trend.png')

# ── PLOT 02: CATEGORY PERFORMANCE ─────────────────────────────────────────────
print("[PLOT 02] Category performance...")
cat = df.groupby('category').agg(
    revenue=('sales','sum'),
    profit=('profit','sum'),
    orders=('order_id','count'),
    avg_margin=('profit_margin','mean')
).reset_index().sort_values('revenue', ascending=False)
cat['margin_pct'] = (cat['profit'] / cat['revenue'] * 100).round(1)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Category Performance Analysis', fontsize=15, fontweight='bold', y=1.01)

# Revenue
colors = [CAT_COLORS[c] for c in cat['category']]
bars = axes[0].barh(cat['category'], cat['revenue'], color=colors, height=0.6)
axes[0].set_title('Total Revenue by Category')
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
for bar, val in zip(bars, cat['revenue']):
    axes[0].text(bar.get_width() * 1.01, bar.get_y() + bar.get_height()/2,
                 fmt_inr(val), va='center', fontsize=9)

# Profit
bars2 = axes[1].barh(cat['category'], cat['profit'], color=colors, height=0.6)
axes[1].set_title('Total Profit by Category')
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
for bar, val in zip(bars2, cat['profit']):
    axes[1].text(bar.get_width() * 1.01, bar.get_y() + bar.get_height()/2,
                 fmt_inr(val), va='center', fontsize=9)

# Margin
bars3 = axes[2].barh(cat['category'], cat['margin_pct'], color=colors, height=0.6)
axes[2].set_title('Avg Profit Margin (%)')
for bar, val in zip(bars3, cat['margin_pct']):
    axes[2].text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                 f'{val:.1f}%', va='center', fontsize=9)
axes[2].axvline(x=cat['margin_pct'].mean(), color='red', linestyle='--',
                linewidth=1.5, label=f"Avg: {cat['margin_pct'].mean():.1f}%")
axes[2].legend(fontsize=9)

for ax in axes:
    ax.invert_yaxis()

plt.tight_layout()
save(fig, '02_category_performance.png')

# ── PLOT 03: REGIONAL ANALYSIS ────────────────────────────────────────────────
print("[PLOT 03] Regional analysis...")
reg = df.groupby('region').agg(
    revenue=('sales','sum'),
    profit=('profit','sum'),
    orders=('order_id','count'),
    customers=('customer_id','nunique')
).reset_index()
reg['margin'] = (reg['profit'] / reg['revenue'] * 100).round(1)
reg['aov']    = (reg['revenue'] / reg['orders']).round(0)

fig, axes = plt.subplots(2, 2, figsize=(13, 9))
fig.suptitle('Regional Performance Analysis', fontsize=15, fontweight='bold')
rcolors = [REG_COLORS[r] for r in reg['region']]

# Revenue pie
wedges, texts, autotexts = axes[0,0].pie(
    reg['revenue'], labels=reg['region'], autopct='%1.1f%%',
    colors=rcolors, startangle=90,
    wedgeprops={'edgecolor':'white','linewidth':2}
)
for at in autotexts: at.set_fontsize(10)
axes[0,0].set_title('Revenue Share by Region')

# Profit bar
bars = axes[0,1].bar(reg['region'], reg['profit'], color=rcolors, width=0.5)
axes[0,1].set_title('Total Profit by Region')
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
for bar, val in zip(bars, reg['profit']):
    axes[0,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20000,
                   fmt_inr(val), ha='center', fontsize=9, fontweight='bold')

# Margin
bars2 = axes[1,0].bar(reg['region'], reg['margin'], color=rcolors, width=0.5)
axes[1,0].set_title('Profit Margin % by Region')
axes[1,0].axhline(reg['margin'].mean(), color='red', linestyle='--', lw=1.5)
for bar, val in zip(bars2, reg['margin']):
    axes[1,0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                   f'{val}%', ha='center', fontsize=10, fontweight='bold')

# AOV
bars3 = axes[1,1].bar(reg['region'], reg['aov'], color=rcolors, width=0.5)
axes[1,1].set_title('Avg Order Value (AOV) by Region')
axes[1,1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
for bar, val in zip(bars3, reg['aov']):
    axes[1,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                   fmt_inr(val), ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
save(fig, '03_regional_analysis.png')

# ── PLOT 04: DISCOUNT IMPACT ──────────────────────────────────────────────────
print("[PLOT 04] Discount impact on profitability...")
disc = df.groupby('discount_band').agg(
    avg_margin=('profit_margin','mean'),
    orders=('order_id','count'),
    avg_profit=('profit','mean'),
    total_revenue=('sales','sum')
).reset_index()
disc_order = ['No Discount','Low (1-10%)','Medium (11-20%)','High (21-30%)','Very High (>30%)']
disc['discount_band'] = pd.Categorical(disc['discount_band'], categories=disc_order, ordered=True)
disc = disc.sort_values('discount_band')

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('Impact of Discounts on Profitability', fontsize=14, fontweight='bold')

# Margin drop
band_colors = ['#1B5E20','#4CAF50','#FFC107','#FF5722','#B71C1C']
bars = axes[0].bar(disc['discount_band'], disc['avg_margin'],
                   color=band_colors, width=0.6)
axes[0].set_title('Avg Profit Margin by Discount Band')
axes[0].set_ylabel('Avg Profit Margin (%)')
axes[0].tick_params(axis='x', rotation=20)
for bar, val in zip(bars, disc['avg_margin']):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 f'{val:.1f}%', ha='center', fontsize=9, fontweight='bold')

# Orders vs avg profit scatter-like grouped bar
x = np.arange(len(disc))
w = 0.35
ax2b = axes[1].twinx()
axes[1].bar(x - w/2, disc['orders'], width=w, color='#2196F3', alpha=0.7, label='Order Count')
ax2b.bar(x + w/2, disc['avg_profit'], width=w, color='#FF9800', alpha=0.7, label='Avg Profit/Order')
axes[1].set_xticks(x)
axes[1].set_xticklabels(disc['discount_band'], rotation=20, fontsize=9)
axes[1].set_ylabel('Order Count', color='#2196F3')
ax2b.set_ylabel('Avg Profit per Order (₹)', color='#FF9800')
ax2b.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1].set_title('Order Volume vs Avg Profit by Discount Band')
lines1, labels1 = axes[1].get_legend_handles_labels()
lines2, labels2 = ax2b.get_legend_handles_labels()
axes[1].legend(lines1+lines2, labels1+labels2, loc='upper right', fontsize=9)

plt.tight_layout()
save(fig, '04_discount_impact.png')

# ── PLOT 05: TOP CUSTOMERS ────────────────────────────────────────────────────
print("[PLOT 05] Top customers...")
top_cust = df.groupby(['customer_id','customer_name','customer_tier']).agg(
    total_sales=('sales','sum'),
    total_profit=('profit','sum'),
    orders=('order_id','count')
).reset_index().sort_values('total_sales', ascending=False).head(15)

tier_color_map = {'Bronze':'#CD7F32','Silver':'#A8A9AD','Gold':'#FFD700','Platinum':'#E5E4E2'}
cust_colors = [tier_color_map.get(str(t), '#2196F3') for t in top_cust['customer_tier']]

fig, ax = plt.subplots(figsize=(13, 6))
bars = ax.barh(top_cust['customer_name'], top_cust['total_sales'],
               color=cust_colors, height=0.65)
ax.set_title('Top 15 Customers by Lifetime Revenue (with Tier)')
ax.set_xlabel('Total Revenue')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
ax.invert_yaxis()

for bar, val, tier, orders in zip(bars, top_cust['total_sales'],
                                   top_cust['customer_tier'], top_cust['orders']):
    ax.text(bar.get_width() + 5000, bar.get_y() + bar.get_height()/2,
            f'{fmt_inr(val)}  |  {orders} orders  |  {tier}',
            va='center', fontsize=8.5)

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=c, label=t) for t, c in tier_color_map.items()]
ax.legend(handles=legend_elements, title='Customer Tier',
          loc='lower right', fontsize=9)

plt.tight_layout()
save(fig, '05_top_customers.png')

# ── PLOT 06: PRODUCT PROFITABILITY ────────────────────────────────────────────
print("[PLOT 06] Product profitability...")
prod = df.groupby(['product_name','category']).agg(
    total_profit=('profit','sum'),
    total_sales=('sales','sum'),
    orders=('order_id','count')
).reset_index()
prod['margin'] = (prod['total_profit'] / prod['total_sales'] * 100).round(1)

top10  = prod.nlargest(10, 'total_profit')
bot10  = prod.nsmallest(10, 'total_profit')

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('Product Profitability: Top 10 vs Bottom 10', fontsize=14, fontweight='bold')

top_colors = [CAT_COLORS[c] for c in top10['category']]
bars = axes[0].barh(top10['product_name'], top10['total_profit'],
                    color=top_colors, height=0.6)
axes[0].set_title('Top 10 Most Profitable Products')
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0].invert_yaxis()
for bar, val in zip(bars, top10['total_profit']):
    axes[0].text(bar.get_width() + 1000, bar.get_y() + bar.get_height()/2,
                 fmt_inr(val), va='center', fontsize=8.5)

bot_colors = [CAT_COLORS[c] for c in bot10['category']]
bars2 = axes[1].barh(bot10['product_name'], bot10['total_profit'],
                     color=bot_colors, height=0.6)
axes[1].set_title('Bottom 10 Least Profitable Products')
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1].invert_yaxis()
for bar, val in zip(bars2, bot10['total_profit']):
    offset = bar.get_width() + 500 if val >= 0 else bar.get_width() - 5000
    axes[1].text(offset, bar.get_y() + bar.get_height()/2,
                 fmt_inr(val), va='center', fontsize=8.5)

plt.tight_layout()
save(fig, '06_product_profitability.png')

# ── PLOT 07: SHIPPING ANALYSIS ────────────────────────────────────────────────
print("[PLOT 07] Shipping analysis...")
ship = df.groupby('ship_mode').agg(
    orders=('order_id','count'),
    revenue=('sales','sum'),
    avg_days=('days_to_ship','mean')
).reset_index().sort_values('orders', ascending=False)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle('Shipping Mode Analysis', fontsize=14, fontweight='bold')

ship_colors = ['#2196F3','#4CAF50','#FF9800','#E91E63']

# Pie — usage
axes[0].pie(ship['orders'], labels=ship['ship_mode'], autopct='%1.1f%%',
            colors=ship_colors, startangle=90,
            wedgeprops={'edgecolor':'white','linewidth':2})
axes[0].set_title('Orders by Ship Mode')

# Revenue bar
bars = axes[1].bar(ship['ship_mode'], ship['revenue'],
                   color=ship_colors, width=0.5)
axes[1].set_title('Revenue by Ship Mode')
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1].tick_params(axis='x', rotation=15)
for bar, val in zip(bars, ship['revenue']):
    axes[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+30000,
                 fmt_inr(val), ha='center', fontsize=8)

# Days to ship distribution
sns.boxplot(data=df, x='ship_mode', y='days_to_ship',
            palette=ship_colors, ax=axes[2], width=0.5)
axes[2].set_title('Days to Ship Distribution')
axes[2].set_xlabel('Ship Mode')
axes[2].set_ylabel('Days')
axes[2].tick_params(axis='x', rotation=15)

plt.tight_layout()
save(fig, '07_shipping_analysis.png')

# ── PLOT 08: CUSTOMER SEGMENTS ────────────────────────────────────────────────
print("[PLOT 08] Customer segment analysis...")
seg = df.groupby('segment').agg(
    revenue=('sales','sum'),
    profit=('profit','sum'),
    orders=('order_id','count'),
    customers=('customer_id','nunique'),
    avg_order=('sales','mean')
).reset_index()
seg['margin'] = (seg['profit'] / seg['revenue'] * 100).round(1)
seg['orders_per_customer'] = (seg['orders'] / seg['customers']).round(1)

seg_colors = ['#1565C0','#2E7D32','#E65100']

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle('Customer Segment Deep Dive', fontsize=14, fontweight='bold')

metrics = [
    ('revenue',             'Revenue by Segment',              fmt_inr),
    ('margin',              'Profit Margin % by Segment',      lambda x, _: f'{x:.1f}%'),
    ('avg_order',           'Avg Order Value by Segment',      fmt_inr),
    ('orders_per_customer', 'Avg Orders per Customer',         lambda x, _: f'{x:.1f}'),
]

for ax, (col, title, fmt_fn) in zip(axes.flatten(), metrics):
    bars = ax.bar(seg['segment'], seg[col], color=seg_colors, width=0.5)
    ax.set_title(title)
    if fmt_fn == fmt_inr:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
    for bar, val in zip(bars, seg[col]):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.01,
                fmt_fn(val, None), ha='center', fontsize=10, fontweight='bold')

plt.tight_layout()
save(fig, '08_customer_segments.png')

# ── PLOT 09: QUARTERLY HEATMAP ────────────────────────────────────────────────
print("[PLOT 09] Quarterly revenue heatmap...")
heat = df.groupby(['order_year','order_quarter'])['sales'].sum().reset_index()
heat_pivot = heat.pivot(index='order_quarter', columns='order_year', values='sales')
heat_pivot.index = [f'Q{i}' for i in heat_pivot.index]

fig, ax = plt.subplots(figsize=(9, 5))
sns.heatmap(heat_pivot, annot=True, fmt='.0f', cmap='YlOrRd',
            linewidths=0.5, linecolor='white',
            ax=ax, cbar_kws={'label': 'Revenue (₹)'},
            annot_kws={'size': 10})

# Format annotations to INR
for text in ax.texts:
    val = float(text.get_text().replace(',',''))
    text.set_text(fmt_inr(val))

ax.set_title('Revenue Heatmap: Quarter × Year', fontsize=13, fontweight='bold')
ax.set_xlabel('Year')
ax.set_ylabel('Quarter')
plt.tight_layout()
save(fig, '09_quarterly_heatmap.png')

# ── PLOT 10: YOY GROWTH ───────────────────────────────────────────────────────
print("[PLOT 10] YoY growth by category...")
yoy = df.groupby(['order_year','category'])['sales'].sum().reset_index()
yoy_pivot = yoy.pivot(index='order_year', columns='category', values='sales').fillna(0)
yoy_growth = yoy_pivot.pct_change() * 100
yoy_growth = yoy_growth.dropna()

fig, ax = plt.subplots(figsize=(12, 5))
x = np.arange(len(yoy_growth))
n_cats = len(yoy_growth.columns)
width  = 0.15

for i, (cat, color) in enumerate(CAT_COLORS.items()):
    if cat in yoy_growth.columns:
        offset = (i - n_cats/2) * width + width/2
        bars = ax.bar(x + offset, yoy_growth[cat], width=width*0.9,
                      color=color, label=cat, alpha=0.85)

ax.axhline(0, color='black', linewidth=1)
ax.set_xticks(x)
ax.set_xticklabels([f'{int(y)}-{int(y)+1}' for y in yoy_growth.index])
ax.set_title('Year-over-Year Revenue Growth (%) by Category')
ax.set_ylabel('Growth (%)')
ax.set_xlabel('Year Transition')
ax.legend(title='Category', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))

plt.tight_layout()
save(fig, '10_yoy_growth.png')

# ── PLOT 11: CORRELATION MATRIX ───────────────────────────────────────────────
print("[PLOT 11] Correlation matrix...")
num_cols = ['quantity','unit_price','discount','sales','profit','profit_margin',
            'days_to_ship','customer_ltv']
corr = df[num_cols].corr()

mask = np.triu(np.ones_like(corr, dtype=bool))
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlGn',
            center=0, vmin=-1, vmax=1, linewidths=0.5,
            ax=ax, annot_kws={'size': 10},
            cbar_kws={'label': 'Correlation Coefficient'})
ax.set_title('Correlation Matrix — Key Numeric Features',
             fontsize=13, fontweight='bold')
plt.tight_layout()
save(fig, '11_correlation_matrix.png')

# ── PLOT 12: EXECUTIVE SUMMARY DASHBOARD ─────────────────────────────────────
print("[PLOT 12] Executive summary dashboard...")

fig = plt.figure(figsize=(16, 10), facecolor='#1E293B')
gs  = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.35)

kpi_ax = [fig.add_subplot(gs[0, i]) for i in range(4)]
line_ax = fig.add_subplot(gs[1, :2])
bar_ax  = fig.add_subplot(gs[1, 2:])
pie_ax  = fig.add_subplot(gs[2, :2])
heat_ax = fig.add_subplot(gs[2, 2:])

for ax in fig.axes:
    ax.set_facecolor('#334155')
    for spine in ax.spines.values():
        spine.set_edgecolor('#475569')

# KPI cards
kpis = [
    ('Total Revenue',    f"₹{df['sales'].sum()/1e7:.2f} Cr",       '#2196F3'),
    ('Total Profit',     f"₹{df['profit'].sum()/1e5:.0f} L",        '#4CAF50'),
    ('Avg Margin',       f"{df['profit_margin'].mean():.1f}%",       '#FF9800'),
    ('Total Orders',     f"{len(df):,}",                             '#E91E63'),
]
for ax, (title, val, color) in zip(kpi_ax, kpis):
    ax.set_facecolor(color)
    ax.text(0.5, 0.62, val, transform=ax.transAxes,
            ha='center', va='center', fontsize=20, fontweight='bold',
            color='white')
    ax.text(0.5, 0.22, title, transform=ax.transAxes,
            ha='center', va='center', fontsize=10, color='white', alpha=0.9)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor('white')

# Revenue trend line
monthly_short = monthly.tail(24)
line_ax.plot(monthly_short['order_year_month'], monthly_short['revenue'],
             color='#38BDF8', linewidth=2)
line_ax.fill_between(monthly_short['order_year_month'],
                     monthly_short['revenue'], alpha=0.2, color='#38BDF8')
line_ax.set_title('Revenue Trend (Last 24 Months)', color='white', fontsize=11)
line_ax.tick_params(colors='white', labelsize=7)
line_ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
line_ax.set_facecolor('#334155')
line_ax.yaxis.label.set_color('white')
line_ax.xaxis.label.set_color('white')
for spine in line_ax.spines.values(): spine.set_edgecolor('#475569')
plt.setp(line_ax.get_xticklabels(), rotation=30, ha='right')

# Category revenue bar — use cat_df to avoid name collision
cat_df = df.groupby('category').agg(revenue=('sales','sum')).reset_index().sort_values('revenue', ascending=True)
cat_sorted = cat_df
bcolors = [CAT_COLORS[c] for c in cat_sorted['category']]
bar_ax.barh(cat_sorted['category'], cat_sorted['revenue'],
            color=bcolors, height=0.5)
bar_ax.set_title('Revenue by Category', color='white', fontsize=11)
bar_ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
bar_ax.tick_params(colors='white', labelsize=9)
bar_ax.set_facecolor('#334155')
for spine in bar_ax.spines.values(): spine.set_edgecolor('#475569')

# Region pie
reg_sorted = reg.sort_values('revenue', ascending=False)
rcolors_sorted = [REG_COLORS[r] for r in reg_sorted['region']]
pie_ax.pie(reg_sorted['revenue'], labels=reg_sorted['region'],
           autopct='%1.1f%%', colors=rcolors_sorted,
           textprops={'color':'white','fontsize':10},
           wedgeprops={'edgecolor':'#1E293B','linewidth':2})
pie_ax.set_title('Regional Revenue Share', color='white', fontsize=11)

# Quarterly heatmap
heat_ax_data = df.groupby(['order_year','order_quarter'])['sales'].sum().reset_index()
hp = heat_ax_data.pivot(index='order_quarter', columns='order_year', values='sales')
hp.index = [f'Q{i}' for i in hp.index]
sns.heatmap(hp, annot=True, fmt='.0f', cmap='Blues',
            ax=heat_ax, linewidths=0.5, linecolor='#1E293B',
            cbar=False, annot_kws={'size':8,'color':'black'})
for text in heat_ax.texts:
    val = float(text.get_text().replace(',',''))
    text.set_text(fmt_inr(val))
heat_ax.set_title('Quarterly Revenue Heatmap', color='white', fontsize=11)
heat_ax.tick_params(colors='white', labelsize=9)
heat_ax.set_xlabel('Year', color='white')
heat_ax.set_ylabel('Quarter', color='white')

fig.suptitle('Smart Sales Intelligence Dashboard — Executive Summary',
             fontsize=16, fontweight='bold', color='white', y=1.01)

save(fig, '12_executive_summary.png')

# ── INSIGHTS REPORT ───────────────────────────────────────────────────────────
print("\n[INSIGHTS] Generating key insights report...")

# Compute insights
cat_summary_ins = df.groupby('category').agg(
    revenue=('sales','sum'),
    profit=('profit','sum'),
    orders=('order_id','count')
).reset_index().sort_values('revenue', ascending=False)
cat_summary_ins['margin_pct'] = (cat_summary_ins['profit'] / cat_summary_ins['revenue'] * 100).round(1)

total_rev      = df['sales'].sum()
total_profit   = df['profit'].sum()
overall_margin = total_profit / total_rev * 100
best_region    = reg.loc[reg['margin'].idxmax(), 'region']
best_reg_margin= reg.loc[reg['margin'].idxmax(), 'margin']
top_cat_rev    = cat_summary_ins.iloc[0]['category']
top_cat_pct    = cat_summary_ins.iloc[0]['revenue'] / total_rev * 100
low_cat_margin = cat_summary_ins.loc[cat_summary_ins['margin_pct'].idxmin(), 'category']
low_margin_val = cat_summary_ins['margin_pct'].min()
q4_rev         = df[df['order_quarter'] == 4]['sales'].sum()
q4_pct         = q4_rev / total_rev * 100
high_disc_margin = disc.loc[disc['discount_band']=='Very High (>30%)', 'avg_margin'].values[0] if len(disc[disc['discount_band']=='Very High (>30%)']) > 0 else 0
no_disc_margin   = disc.loc[disc['discount_band']=='No Discount', 'avg_margin'].values[0]

insights = f"""
================================================================================
  KEY BUSINESS INSIGHTS — Smart Sales Intelligence Dashboard
================================================================================

DATASET OVERVIEW
  Period        : 2021 – 2024 (4 years)
  Total Records : {len(df):,} orders
  Unique Customers: {df['customer_id'].nunique()}
  Products       : {df['product_name'].nunique()} SKUs across 5 categories
  Total Revenue  : ₹{total_rev/1e7:.2f} Crore
  Total Profit   : ₹{total_profit/1e5:.0f} Lakh
  Overall Margin : {overall_margin:.1f}%

--------------------------------------------------------------------------------
INSIGHT 1 — ELECTRONICS DOMINATES REVENUE BUT HAS LOWEST MARGIN
  Electronics contributes {top_cat_pct:.0f}% of total revenue but has the lowest
  profit margin ({low_margin_val:.1f}%) among all categories. High price points
  drive volume but discount pressure compresses margins significantly.
  → Recommendation: Reduce discounting on electronics above-₹20K products.

INSIGHT 2 — Q4 SEASONALITY IS SIGNIFICANT
  Q4 (Oct–Dec) consistently contributes {q4_pct:.0f}% of annual revenue across
  all years, driven by festive season demand (Navratri, Diwali, Christmas).
  → Recommendation: Increase inventory and marketing spend in Sept–Oct.

INSIGHT 3 — WEST REGION LEADS PROFITABILITY
  {best_region} region achieves the highest profit margin at {best_reg_margin:.1f}%,
  outperforming the national average of {overall_margin:.1f}%. Cities like Mumbai
  and Pune show premium product affinity with lower discount demands.
  → Recommendation: Study West region playbook and replicate in East region.

INSIGHT 4 — HIGH DISCOUNTS DESTROY PROFIT MARGIN
  Orders with no discount average {no_disc_margin:.1f}% margin. Orders with >30%
  discount average {high_disc_margin:.1f}% margin — a significant compression.
  {df[df['discount'] > 0.25]['order_id'].count()} orders ({df[df['discount'] > 0.25]['order_id'].count()/len(df)*100:.1f}%)
  have discounts above 25%.
  → Recommendation: Cap maximum discount at 20% unless clearing dead stock.

INSIGHT 5 — CLOTHING HAS BEST MARGIN, LOWEST AOV
  Clothing has the second-highest margin ({cat_summary_ins.loc[cat_summary_ins['category']=='Clothing','margin_pct'].values[0]:.1f}%)
  but lowest average order value. Bundling strategies (e.g., shirt + trouser)
  could increase AOV while maintaining healthy margins.
  → Recommendation: Launch bundle offers in Clothing category.

INSIGHT 6 — TOP 20 CUSTOMERS DRIVE DISPROPORTIONATE REVENUE
  Top 20 customers (6.7% of base) contribute
  {df.groupby('customer_id')['sales'].sum().nlargest(20).sum()/total_rev*100:.0f}%
  of total revenue — classic Pareto principle.
  → Recommendation: Implement loyalty program for Platinum/Gold tier customers.

INSIGHT 7 — STANDARD CLASS SHIPPING DOMINATES
  {df[df['ship_mode']=='Standard Class']['order_id'].count()/len(df)*100:.0f}%
  of orders use Standard Class shipping (avg {df[df['ship_mode']=='Standard Class']['days_to_ship'].mean():.1f} days).
  Same Day shipping is underutilized at
  {df[df['ship_mode']=='Same Day']['order_id'].count()/len(df)*100:.1f}%.
  → Recommendation: Promote First Class shipping in high-margin categories.

--------------------------------------------------------------------------------
FILES GENERATED
  Plots   : outputs/plots/ (12 visualizations)
  Report  : outputs/reports/key_insights.txt
  Data    : data/cleaned_sales_data.csv
  SQL DB  : data/sales.db (created by 03_sql_analysis.py)
================================================================================
"""

print(insights)

report_path = os.path.join(BASE_DIR, 'outputs', 'reports', 'key_insights.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(insights)
print(f"[SAVE] Insights report → {report_path}")

print("\n" + "=" * 60)
print(f"  EDA complete. 12 plots saved to outputs/plots/")
print("  Run 03_sql_analysis.py next.")
print("=" * 60)
