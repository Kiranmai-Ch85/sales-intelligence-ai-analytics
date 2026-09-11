"""
Dataset Generator for Smart Sales Intelligence Dashboard
Generates 5000 realistic retail sales records with built-in patterns:
- Seasonal trends (Q4 spike)
- Regional performance differences
- Category profit margin variations
- Customer loyalty tiers
- Discount impact on profit
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# ── CONFIG ────────────────────────────────────────────────────────────────────
N_RECORDS = 5000
START_DATE = datetime(2021, 1, 1)
END_DATE   = datetime(2024, 12, 31)

REGIONS = ['North', 'South', 'East', 'West']

CATEGORIES = {
    'Electronics': {
        'products': [
            ('Laptop Pro 15"',        55000, 0.22),
            ('Laptop Air 13"',        42000, 0.20),
            ('Smartphone X12',        18000, 0.18),
            ('Smartphone Lite',       10000, 0.15),
            ('Tablet Ultra',          25000, 0.21),
            ('Wireless Earbuds',       3500, 0.30),
            ('Smartwatch Series 5',    8000, 0.25),
            ('Monitor 27" 4K',        22000, 0.19),
            ('Mechanical Keyboard',    4500, 0.35),
            ('USB-C Hub',              1800, 0.40),
        ],
        'base_discount': 0.08,
    },
    'Clothing': {
        'products': [
            ('Men\'s Formal Shirt',    1200, 0.55),
            ('Women\'s Kurti',         1500, 0.52),
            ('Denim Jeans',            2200, 0.48),
            ('Winter Jacket',          4500, 0.45),
            ('Sports T-Shirt',          800, 0.60),
            ('Ethnic Saree',           3500, 0.50),
            ('Sneakers Classic',       3200, 0.42),
            ('Formal Trousers',        1800, 0.50),
            ('Casual Dress',           2500, 0.53),
            ('Woollen Sweater',        2000, 0.47),
        ],
        'base_discount': 0.12,
    },
    'Home & Kitchen': {
        'products': [
            ('Air Fryer 4L',           5500, 0.38),
            ('Mixer Grinder 750W',     3200, 0.35),
            ('Pressure Cooker 5L',     2100, 0.40),
            ('Non-Stick Cookware Set', 3800, 0.36),
            ('Water Purifier RO',      9500, 0.28),
            ('Vacuum Cleaner',         6500, 0.30),
            ('Bedsheet Set King',      1800, 0.55),
            ('Sofa Cushion Set',       1200, 0.58),
            ('Wall Clock Wooden',       850, 0.62),
            ('LED Desk Lamp',          1500, 0.45),
        ],
        'base_discount': 0.10,
    },
    'Books & Stationery': {
        'products': [
            ('Data Science Handbook',   650, 0.40),
            ('Python Programming',      580, 0.38),
            ('MBA Case Studies',        750, 0.42),
            ('Novel - Bestseller',      350, 0.45),
            ('Notebook Premium A4',     220, 0.50),
            ('Planner 2024',            380, 0.48),
            ('Sketch Pad A3',           450, 0.46),
            ('Pen Set Luxury',          680, 0.52),
            ('Highlighter Pack',        180, 0.55),
            ('Sticky Notes Bulk',       120, 0.60),
        ],
        'base_discount': 0.15,
    },
    'Sports & Fitness': {
        'products': [
            ('Yoga Mat Premium',       1800, 0.45),
            ('Dumbbells 10kg Pair',    2500, 0.38),
            ('Resistance Bands Set',    950, 0.52),
            ('Cycling Helmet',         2200, 0.40),
            ('Running Shoes Pro',      4500, 0.35),
            ('Badminton Racket Set',   1500, 0.42),
            ('Cricket Bat SS',         3200, 0.38),
            ('Football Nike',          1800, 0.40),
            ('Protein Powder 2kg',     2800, 0.30),
            ('Jump Rope Speed',         450, 0.58),
        ],
        'base_discount': 0.08,
    },
}

CITIES = {
    'North': ['Delhi', 'Chandigarh', 'Jaipur', 'Lucknow', 'Amritsar'],
    'South': ['Bangalore', 'Chennai', 'Hyderabad', 'Kochi', 'Coimbatore'],
    'East':  ['Kolkata', 'Bhubaneswar', 'Patna', 'Guwahati', 'Ranchi'],
    'West':  ['Mumbai', 'Pune', 'Ahmedabad', 'Surat', 'Nagpur'],
}

SEGMENTS = ['Consumer', 'Corporate', 'Home Office']
SHIP_MODES = ['Standard Class', 'Second Class', 'First Class', 'Same Day']

# ── CUSTOMER POOL ─────────────────────────────────────────────────────────────
first_names = [
    'Aarav','Aditi','Akash','Ananya','Arjun','Deepika','Divya','Gaurav',
    'Ishaan','Kavya','Kiran','Manish','Meera','Neha','Nikhil','Pooja',
    'Priya','Rahul','Rajesh','Ravi','Rohit','Sakshi','Sandeep','Sneha',
    'Suresh','Tanvi','Vikas','Vikram','Yash','Zara','Aisha','Amit',
    'Anjali','Bhavesh','Chetan','Dhruv','Esha','Farhan','Geeta','Harsh',
]
last_names = [
    'Sharma','Verma','Patel','Singh','Kumar','Gupta','Joshi','Mehta',
    'Shah','Nair','Reddy','Iyer','Pillai','Chopra','Malhotra','Kapoor',
    'Bose','Das','Chatterjee','Mishra','Tiwari','Pandey','Yadav','Sinha',
]

def generate_customers(n=300):
    customers = []
    for i in range(1, n + 1):
        name  = f"{random.choice(first_names)} {random.choice(last_names)}"
        seg   = np.random.choice(SEGMENTS, p=[0.52, 0.32, 0.16])
        region= random.choice(REGIONS)
        city  = random.choice(CITIES[region])
        customers.append({
            'customer_id': f'CUST-{i:04d}',
            'customer_name': name,
            'segment': seg,
            'region': region,
            'city': city,
        })
    return customers

customers = generate_customers(300)

# ── DATE HELPERS ──────────────────────────────────────────────────────────────
def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def seasonal_weight(dt):
    """Q4 gets 40% more orders; Jan–Feb are slow."""
    m = dt.month
    if m in [11, 12]:   return 1.4
    if m in [9, 10]:    return 1.15
    if m in [7, 8]:     return 1.05
    if m in [1, 2]:     return 0.75
    return 1.0

# ── MAIN GENERATION ───────────────────────────────────────────────────────────
records = []
order_counter = 1

# Pre-build a weighted date pool to reflect seasonality
date_pool = []
d = START_DATE
while d <= END_DATE:
    weight = seasonal_weight(d)
    count  = max(1, int(weight * 4))
    date_pool.extend([d] * count)
    d += timedelta(days=1)

for _ in range(N_RECORDS):
    # Pick customer
    cust = random.choice(customers)

    # Pick order date
    order_date = random.choice(date_pool)
    ship_days  = {'Standard Class': 5, 'Second Class': 3,
                  'First Class': 2, 'Same Day': 0}
    ship_mode  = np.random.choice(
        list(ship_days.keys()), p=[0.58, 0.22, 0.14, 0.06]
    )
    ship_date  = order_date + timedelta(days=ship_days[ship_mode] + random.randint(0, 2))

    # Pick category + product
    category   = np.random.choice(
        list(CATEGORIES.keys()), p=[0.30, 0.25, 0.20, 0.10, 0.15]
    )
    cat_data   = CATEGORIES[category]
    prod_name, base_price, base_margin = random.choice(cat_data['products'])

    # Quantity
    quantity   = np.random.choice([1, 2, 3, 4, 5], p=[0.50, 0.25, 0.13, 0.08, 0.04])

    # Discount — sometimes large discounts eat into profit (intentional pattern)
    base_disc  = cat_data['base_discount']
    discount   = round(np.random.choice(
        [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        p=[0.30, 0.18, 0.16, 0.12, 0.10, 0.07, 0.04, 0.02, 0.01]
    ), 2)

    # Price with slight variation
    price_var  = base_price * np.random.uniform(0.95, 1.05)
    unit_price = round(price_var, 2)
    sales      = round(unit_price * quantity * (1 - discount), 2)

    # Profit — discount reduces margin significantly above 20%
    margin_hit = 1 - (discount * 1.8)  # discounts compress margin
    profit_margin = base_margin * margin_hit
    profit     = round(sales * profit_margin, 2)

    # Region-based performance tweak (West performs best, East struggles)
    region_multiplier = {'North': 1.0, 'South': 1.05, 'East': 0.92, 'West': 1.10}
    profit = round(profit * region_multiplier[cust['region']], 2)

    records.append({
        'order_id':       f'ORD-{order_counter:05d}',
        'order_date':     order_date.strftime('%Y-%m-%d'),
        'ship_date':      ship_date.strftime('%Y-%m-%d'),
        'ship_mode':      ship_mode,
        'customer_id':    cust['customer_id'],
        'customer_name':  cust['customer_name'],
        'segment':        cust['segment'],
        'region':         cust['region'],
        'city':           cust['city'],
        'category':       category,
        'product_name':   prod_name,
        'quantity':       quantity,
        'unit_price':     unit_price,
        'discount':       discount,
        'sales':          sales,
        'profit':         profit,
        'profit_margin':  round(profit / sales * 100 if sales > 0 else 0, 2),
    })
    order_counter += 1

df = pd.DataFrame(records)
df = df.sort_values('order_date').reset_index(drop=True)

out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_sales_data.csv')
df.to_csv(out_path, index=False)

print(f"Dataset generated: {len(df)} records")
print(f"Date range: {df['order_date'].min()} → {df['order_date'].max()}")
print(f"Categories: {df['category'].value_counts().to_dict()}")
print(f"Regions: {df['region'].value_counts().to_dict()}")
print(f"Total Sales: ₹{df['sales'].sum():,.0f}")
print(f"Total Profit: ₹{df['profit'].sum():,.0f}")
print(f"Avg Profit Margin: {df['profit_margin'].mean():.1f}%")
print(f"\nSaved to: {os.path.abspath(out_path)}")
