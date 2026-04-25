"""
Levi's-style CRM Sample Data Generator
Creates 6 interconnected tables for realistic business analytics:
1. customers - Customer master data
2. products - Product catalog (jeans, jackets, etc.)
3. stores - Physical + online store locations
4. orders - Order transactions
5. order_items - Line items per order (for product-level analysis)
6. campaigns - Marketing campaigns

Total: ~50,000 rows across all tables
"""

import os
import psycopg2
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ==================== CONFIG ====================
NUM_CUSTOMERS = 2000
NUM_PRODUCTS = 80
NUM_STORES = 25
NUM_ORDERS = 15000
NUM_CAMPAIGNS = 30

# ==================== REFERENCE DATA ====================

# Indian + global cities for Levi's-style brand
CITIES = [
    ('Mumbai', 'Maharashtra', 'India', 'West'),
    ('Delhi', 'Delhi', 'India', 'North'),
    ('Bangalore', 'Karnataka', 'India', 'South'),
    ('Chennai', 'Tamil Nadu', 'India', 'South'),
    ('Hyderabad', 'Telangana', 'India', 'South'),
    ('Pune', 'Maharashtra', 'India', 'West'),
    ('Kolkata', 'West Bengal', 'India', 'East'),
    ('Ahmedabad', 'Gujarat', 'India', 'West'),
    ('Jaipur', 'Rajasthan', 'India', 'North'),
    ('Lucknow', 'Uttar Pradesh', 'India', 'North'),
    ('Chandigarh', 'Punjab', 'India', 'North'),
    ('Indore', 'Madhya Pradesh', 'India', 'Central'),
    ('Surat', 'Gujarat', 'India', 'West'),
    ('Dubai', 'Dubai', 'UAE', 'Middle East'),
    ('Singapore', 'Singapore', 'Singapore', 'Asia'),
]

# Product categories for Levi's
PRODUCT_CATEGORIES = {
    'Jeans': [
        ('501 Original Fit', 4999), ('511 Slim Fit', 4499), ('512 Slim Tapered', 4299),
        ('513 Slim Straight', 3999), ('514 Straight', 3799), ('527 Slim Bootcut', 4199),
        ('541 Athletic Taper', 4399), ('551Z Authentic Straight', 5499),
        ('Mile High Super Skinny', 3999), ('Wedgie Straight', 4299),
        ('Ribcage Straight Ankle', 4799), ('721 High Rise Skinny', 3999),
    ],
    'Shirts': [
        ('Classic Western Shirt', 2999), ('Barstow Western Shirt', 3499),
        ('Sunset One Pocket Shirt', 2799), ('Battery Housemark Slim', 1999),
        ('Original Housemark Tee', 1499), ('Logo Crew Sweatshirt', 2499),
        ('Standard Polo Shirt', 1999), ('Long Sleeve Pocket Tee', 1799),
    ],
    'Jackets': [
        ('Trucker Jacket Original', 5999), ('Sherpa Trucker Jacket', 7499),
        ('Type III Trucker', 6499), ('Vintage Fit Trucker', 5799),
        ('Lightweight Trucker', 4999), ('Type 3 Sherpa Trucker', 8999),
    ],
    'Accessories': [
        ('Leather Belt Classic', 1999), ('Reversible Belt', 2299),
        ('Trucker Cap Logo', 999), ('Beanie Cap', 799),
        ('Canvas Tote Bag', 1499), ('Leather Wallet', 1799),
    ],
    'Footwear': [
        ('Classic Sneakers', 3999), ('Canvas Low Tops', 2999),
        ('Chukka Boots', 5999), ('Loafers', 4499),
    ],
    'Kids': [
        ('Kids 511 Slim Fit', 2299), ('Kids Trucker Jacket', 3299),
        ('Kids Logo Tee', 899), ('Kids Pull-on Jeans', 1999),
    ],
}

# Customer segments
CUSTOMER_SEGMENTS = ['Premium', 'Regular', 'Occasional', 'New', 'VIP']
ACQUISITION_CHANNELS = ['Organic Search', 'Paid Ads', 'Referral', 'Social Media', 'Walk-in', 'Email Campaign']

# First/Last names for realistic Indian customers
FIRST_NAMES = [
    'Aarav', 'Aditi', 'Akash', 'Ananya', 'Arjun', 'Aisha', 'Amit', 'Anita',
    'Bharat', 'Bhavna', 'Chandan', 'Deepika', 'Dev', 'Divya', 'Gaurav', 'Geetha',
    'Harsh', 'Ishita', 'Jay', 'Kavita', 'Kunal', 'Lakshmi', 'Mohit', 'Meera',
    'Nikhil', 'Nisha', 'Pooja', 'Pranav', 'Priya', 'Rahul', 'Rajesh', 'Riya',
    'Rohan', 'Sneha', 'Suresh', 'Swati', 'Tanvi', 'Tarun', 'Vikram', 'Vishal',
    'Yash', 'Zoya', 'Parveen', 'Radhika', 'Sanjay', 'Neha', 'Karan', 'Simran'
]

LAST_NAMES = [
    'Sharma', 'Kumar', 'Singh', 'Patel', 'Verma', 'Gupta', 'Mehta', 'Jain',
    'Agarwal', 'Reddy', 'Nair', 'Iyer', 'Khanna', 'Kapoor', 'Malhotra', 'Bose',
    'Banerjee', 'Mukherjee', 'Chatterjee', 'Sen', 'Das', 'Joshi', 'Bhatt', 'Rao'
]

# Marketing campaign names
CAMPAIGN_TYPES = [
    ('Summer Sale', 'Seasonal'), ('Winter Collection', 'Seasonal'),
    ('Republic Day Offer', 'Festival'), ('Independence Day Sale', 'Festival'),
    ('Diwali Bonanza', 'Festival'), ('Black Friday', 'Festival'),
    ('501 Day Special', 'Brand'), ('Denim Festival', 'Brand'),
    ('New Arrivals', 'Product Launch'), ('Clearance Sale', 'Discount'),
    ('Member Exclusive', 'Loyalty'), ('First Purchase Discount', 'Acquisition'),
    ('Refer a Friend', 'Referral'), ('App Launch Offer', 'Digital'),
    ('Insta Special', 'Social Media'),
]


def create_tables(conn):
    """Create all 6 tables with proper relationships."""
    sql = """
    -- Drop existing tables (in correct order due to foreign keys)
    DROP TABLE IF EXISTS order_items CASCADE;
    DROP TABLE IF EXISTS orders CASCADE;
    DROP TABLE IF EXISTS campaigns CASCADE;
    DROP TABLE IF EXISTS products CASCADE;
    DROP TABLE IF EXISTS customers CASCADE;
    DROP TABLE IF EXISTS stores CASCADE;
    
    -- ============ CUSTOMERS ============
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        gender TEXT CHECK (gender IN ('Male', 'Female', 'Other')),
        date_of_birth DATE,
        city TEXT NOT NULL,
        state TEXT,
        country TEXT,
        signup_date DATE NOT NULL,
        segment TEXT CHECK (segment IN ('Premium', 'Regular', 'Occasional', 'New', 'VIP')),
        acquisition_channel TEXT,
        loyalty_points INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    -- ============ STORES ============
    CREATE TABLE stores (
        store_id TEXT PRIMARY KEY,
        store_name TEXT NOT NULL,
        store_type TEXT CHECK (store_type IN ('Flagship', 'Standard', 'Outlet', 'Online', 'Pop-up')),
        city TEXT NOT NULL,
        state TEXT,
        country TEXT,
        region TEXT,
        opening_date DATE,
        store_manager TEXT,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    -- ============ PRODUCTS ============
    CREATE TABLE products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        sub_category TEXT,
        sku TEXT UNIQUE,
        size TEXT,
        color TEXT,
        price NUMERIC(10, 2) NOT NULL,
        cost NUMERIC(10, 2),
        launch_date DATE,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    -- ============ CAMPAIGNS ============
    CREATE TABLE campaigns (
        campaign_id TEXT PRIMARY KEY,
        campaign_name TEXT NOT NULL,
        campaign_type TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        budget NUMERIC(12, 2),
        discount_percentage NUMERIC(5, 2),
        target_segment TEXT,
        channel TEXT
    );
    
    -- ============ ORDERS ============
    CREATE TABLE orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT REFERENCES customers(customer_id),
        store_id TEXT REFERENCES stores(store_id),
        campaign_id TEXT REFERENCES campaigns(campaign_id),
        order_date TIMESTAMP NOT NULL,
        delivery_date TIMESTAMP,
        status TEXT CHECK (status IN ('DELIVERED', 'SHIPPED', 'CANCELLED', 'PENDING', 'RETURNED')),
        payment_method TEXT CHECK (payment_method IN ('Card', 'UPI', 'Cash', 'Net Banking', 'Wallet', 'EMI')),
        total_amount NUMERIC(12, 2) NOT NULL,
        discount_amount NUMERIC(10, 2) DEFAULT 0,
        tax_amount NUMERIC(10, 2),
        shipping_charge NUMERIC(8, 2) DEFAULT 0,
        is_online BOOLEAN
    );
    
    -- ============ ORDER ITEMS ============
    CREATE TABLE order_items (
        item_id SERIAL PRIMARY KEY,
        order_id TEXT REFERENCES orders(order_id),
        product_id TEXT REFERENCES products(product_id),
        quantity INTEGER NOT NULL,
        unit_price NUMERIC(10, 2) NOT NULL,
        discount_per_item NUMERIC(8, 2) DEFAULT 0,
        line_total NUMERIC(12, 2) NOT NULL
    );
    
    -- ============ INDEXES ============
    CREATE INDEX idx_orders_customer ON orders(customer_id);
    CREATE INDEX idx_orders_store ON orders(store_id);
    CREATE INDEX idx_orders_campaign ON orders(campaign_id);
    CREATE INDEX idx_orders_date ON orders(order_date);
    CREATE INDEX idx_orders_status ON orders(status);
    CREATE INDEX idx_items_order ON order_items(order_id);
    CREATE INDEX idx_items_product ON order_items(product_id);
    CREATE INDEX idx_customers_segment ON customers(segment);
    CREATE INDEX idx_customers_city ON customers(city);
    CREATE INDEX idx_products_category ON products(category);
    CREATE INDEX idx_stores_type ON stores(store_type);
    """
    
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("✅ Created 6 tables with indexes + foreign keys")


def generate_customers():
    """Generate customer master data."""
    customers = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years of customer history
    
    for i in range(NUM_CUSTOMERS):
        signup_offset = random.randint(0, 730)
        signup_date = start_date + timedelta(days=signup_offset)
        
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        city_data = random.choice(CITIES)
        
        # DOB: 18-60 years old
        age = random.randint(18, 60)
        dob = end_date - timedelta(days=age*365 + random.randint(0, 365))
        
        # Segment based on signup recency
        days_since_signup = (end_date - signup_date).days
        if days_since_signup < 30:
            segment = 'New'
        elif days_since_signup > 365 and random.random() < 0.15:
            segment = 'VIP'
        else:
            segment = random.choices(
                ['Premium', 'Regular', 'Occasional'],
                weights=[0.2, 0.5, 0.3]
            )[0]
        
        loyalty_points = random.randint(0, 5000) if segment in ['Premium', 'VIP'] else random.randint(0, 1000)
        
        customers.append((
            f'CUST{i+1:05d}',
            first,
            last,
            f"{first.lower()}.{last.lower()}{i}@example.com",
            f"+91{random.randint(7000000000, 9999999999)}",
            random.choices(['Male', 'Female', 'Other'], weights=[0.45, 0.5, 0.05])[0],
            dob.date(),
            city_data[0],  # city
            city_data[1],  # state
            city_data[2],  # country
            signup_date.date(),
            segment,
            random.choice(ACQUISITION_CHANNELS),
            loyalty_points,
            random.random() < 0.92  # 92% active
        ))
    
    return customers


def generate_stores():
    """Generate store master data."""
    stores = []
    end_date = datetime.now()
    
    for i in range(NUM_STORES):
        city_data = random.choice(CITIES)
        store_type = random.choices(
            ['Flagship', 'Standard', 'Outlet', 'Online', 'Pop-up'],
            weights=[0.1, 0.5, 0.2, 0.15, 0.05]
        )[0]
        
        # Online store has only one
        if store_type == 'Online' and i > 0:
            store_type = 'Standard'
        
        opening_date = end_date - timedelta(days=random.randint(180, 1825))
        
        stores.append((
            f'STR{i+1:03d}',
            f"Levi's {city_data[0]} {store_type}" if store_type != 'Online' else "Levi's Online India",
            store_type,
            city_data[0] if store_type != 'Online' else 'Online',
            city_data[1] if store_type != 'Online' else 'Online',
            city_data[2] if store_type != 'Online' else 'India',
            city_data[3] if store_type != 'Online' else 'Online',
            opening_date.date(),
            f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            random.random() < 0.95
        ))
    
    return stores


def generate_products():
    """Generate product catalog."""
    products = []
    end_date = datetime.now()
    sizes = ['28', '30', '32', '34', '36', '38', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'Free Size']
    colors = ['Indigo', 'Black', 'Blue', 'Light Blue', 'Dark Blue', 'White', 'Grey', 'Brown', 'Beige', 'Olive']
    
    product_id = 1
    for category, items in PRODUCT_CATEGORIES.items():
        for name, base_price in items:
            # Variations
            variations = random.randint(1, 3)
            for v in range(variations):
                size = random.choice(sizes) if category != 'Accessories' else 'Free Size'
                color = random.choice(colors)
                price = base_price * random.uniform(0.95, 1.15)
                cost = price * random.uniform(0.35, 0.55)  # 35-55% cost
                launch = end_date - timedelta(days=random.randint(30, 1095))
                
                products.append((
                    f'PROD{product_id:05d}',
                    name,
                    category,
                    f"{category} - {color}" if category in ['Jeans', 'Jackets'] else category,
                    f"LV-{category[:3].upper()}-{product_id:05d}",
                    size,
                    color,
                    round(price, 2),
                    round(cost, 2),
                    launch.date(),
                    random.random() < 0.90
                ))
                product_id += 1
                
                if product_id > NUM_PRODUCTS:
                    return products
    
    return products


def generate_campaigns():
    """Generate marketing campaigns."""
    campaigns = []
    end_date = datetime.now()
    
    for i in range(NUM_CAMPAIGNS):
        campaign_name, campaign_type = random.choice(CAMPAIGN_TYPES)
        start_offset = random.randint(0, 365)
        duration = random.randint(7, 30)
        start = end_date - timedelta(days=start_offset)
        end = start + timedelta(days=duration)
        
        campaigns.append((
            f'CAMP{i+1:03d}',
            f"{campaign_name} {start.year}",
            campaign_type,
            start.date(),
            end.date(),
            random.randint(50000, 1000000),
            random.choice([10, 15, 20, 25, 30, 40, 50]),
            random.choice(CUSTOMER_SEGMENTS),
            random.choice(['Email', 'SMS', 'Social Media', 'In-Store', 'Online'])
        ))
    
    return campaigns


def generate_orders_and_items(customers, stores, products, campaigns):
    """Generate orders + line items."""
    orders = []
    order_items = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    item_id_counter = 1
    
    for i in range(NUM_ORDERS):
        # Random customer (active customers more likely to buy)
        active_customers = [c for c in customers if c[14]]  # is_active
        customer = random.choice(active_customers if active_customers else customers)
        customer_id = customer[0]
        
        # Random store
        active_stores = [s for s in stores if s[9]]  # is_active
        store = random.choice(active_stores)
        store_id = store[0]
        is_online = store[2] == 'Online'
        
        # Random date
        order_date = start_date + timedelta(
            days=random.randint(0, 365),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Status (most delivered)
        status = random.choices(
            ['DELIVERED', 'SHIPPED', 'CANCELLED', 'PENDING', 'RETURNED'],
            weights=[0.72, 0.10, 0.08, 0.05, 0.05]
        )[0]
        
        # Delivery date
        if status in ['DELIVERED', 'SHIPPED', 'RETURNED']:
            delivery_date = order_date + timedelta(days=random.randint(2, 10))
        else:
            delivery_date = None
        
        # Optional campaign
        campaign_id = None
        discount_pct = 0
        if random.random() < 0.35:  # 35% orders use campaign
            campaign = random.choice(campaigns)
            # Check if order_date is within campaign period
            if campaign[3] <= order_date.date() <= campaign[4]:
                campaign_id = campaign[0]
                discount_pct = float(campaign[6])
        
        # Generate 1-5 items per order
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
        active_products = [p for p in products if p[10]]  # is_active
        order_products = random.sample(active_products, min(num_items, len(active_products)))
        
        order_subtotal = 0
        order_total_discount = 0
        
        items_for_this_order = []
        order_id = f'ORD{i+1:06d}'
        
        for product in order_products:
            product_id = product[0]
            unit_price = float(product[7])
            quantity = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
            
            item_discount = 0
            if discount_pct > 0:
                item_discount = round(unit_price * (discount_pct / 100), 2)
            
            line_total = round((unit_price - item_discount) * quantity, 2)
            order_subtotal += unit_price * quantity
            order_total_discount += item_discount * quantity
            
            items_for_this_order.append((
                order_id,
                product_id,
                quantity,
                unit_price,
                item_discount,
                line_total
            ))
            item_id_counter += 1
        
        # Calculate tax + shipping
        tax = round(order_subtotal * 0.18, 2)  # 18% GST
        shipping = 0 if order_subtotal > 2000 or not is_online else 99
        total_amount = round(order_subtotal - order_total_discount + tax + shipping, 2)
        
        orders.append((
            order_id,
            customer_id,
            store_id,
            campaign_id,
            order_date,
            delivery_date,
            status,
            random.choices(
                ['Card', 'UPI', 'Cash', 'Net Banking', 'Wallet', 'EMI'],
                weights=[0.35, 0.30, 0.10, 0.10, 0.10, 0.05]
            )[0],
            total_amount,
            round(order_total_discount, 2),
            tax,
            shipping,
            is_online
        ))
        
        order_items.extend(items_for_this_order)
    
    return orders, order_items


def insert_data(conn, customers, stores, products, campaigns, orders, order_items):
    """Bulk insert all data."""
    
    print(f"\n💾 Inserting {len(customers):,} customers...")
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO customers VALUES 
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            customers
        )
    conn.commit()
    
    print(f"💾 Inserting {len(stores):,} stores...")
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO stores VALUES 
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            stores
        )
    conn.commit()
    
    print(f"💾 Inserting {len(products):,} products...")
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO products VALUES 
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            products
        )
    conn.commit()
    
    print(f"💾 Inserting {len(campaigns):,} campaigns...")
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO campaigns VALUES 
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            campaigns
        )
    conn.commit()
    
    print(f"💾 Inserting {len(orders):,} orders...")
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO orders VALUES 
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            orders
        )
    conn.commit()
    
    print(f"💾 Inserting {len(order_items):,} order items...")
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_per_item, line_total) 
            VALUES (%s,%s,%s,%s,%s,%s)""",
            order_items
        )
    conn.commit()
    
    print("✅ All data inserted!")


def show_stats(conn):
    """Display data overview."""
    queries = [
        ("Total Customers", "SELECT COUNT(*) FROM customers"),
        ("Total Products", "SELECT COUNT(*) FROM products"),
        ("Total Stores", "SELECT COUNT(*) FROM stores"),
        ("Total Campaigns", "SELECT COUNT(*) FROM campaigns"),
        ("Total Orders", "SELECT COUNT(*) FROM orders"),
        ("Total Order Items", "SELECT COUNT(*) FROM order_items"),
        ("Total Revenue (Delivered)", "SELECT SUM(total_amount) FROM orders WHERE status='DELIVERED'"),
        ("Unique Cities", "SELECT COUNT(DISTINCT city) FROM customers"),
        ("Date Range", "SELECT MIN(order_date)::DATE || ' to ' || MAX(order_date)::DATE FROM orders"),
    ]
    
    print("\n" + "=" * 70)
    print("📊 LEVI'S CRM DATA OVERVIEW")
    print("=" * 70)
    
    for label, query in queries:
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()[0]
            if isinstance(result, (int, float)) and label.startswith("Total Revenue"):
                print(f"  {label:30s}  ₹{result:,.2f}")
            else:
                print(f"  {label:30s}  {result}")
    print("=" * 70)


def main():
    db_url = os.getenv('DB_URL')
    if not db_url:
        print("❌ DB_URL not found in .env file")
        return
    
    print("🔌 Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    try:
        print("\n📦 Creating Levi's CRM schema (6 tables)...")
        create_tables(conn)
        
        print("\n🎲 Generating data...")
        customers = generate_customers()
        stores = generate_stores()
        products = generate_products()
        campaigns = generate_campaigns()
        orders, order_items = generate_orders_and_items(customers, stores, products, campaigns)
        
        insert_data(conn, customers, stores, products, campaigns, orders, order_items)
        
        show_stats(conn)
        
        print("\n🎉 Setup complete! Now run: streamlit run app.py")
        print("\n💡 Try these queries:")
        print("   - 'Top 5 cities by revenue'")
        print("   - 'Mumbai store ka monthly sales trend dikhao'")
        print("   - 'VIP customers ka favorite product category'")
        print("   - 'Campaign-wise revenue compare karo with chart'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
