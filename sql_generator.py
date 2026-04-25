"""
SQL Generator v3 — Full Levi's CRM Schema (6 tables with JOINs)
"""

import os
from groq import Groq

# ==================== FULL CRM SCHEMA ====================
SCHEMA_CONTEXT = """
You are a PostgreSQL expert. Generate ONLY a valid PostgreSQL SELECT query.

DATABASE: Levi's CRM Database
============================
You have access to 6 interconnected tables. Use JOINs when needed.

============ TABLE 1: customers ============
Master customer data.
- customer_id (TEXT, PK): Unique customer identifier (CUST00001)
- first_name (TEXT): First name
- last_name (TEXT): Last name
- email (TEXT, UNIQUE): Email address
- phone (TEXT): Phone number
- gender (TEXT): 'Male' / 'Female' / 'Other'
- date_of_birth (DATE): DOB
- city (TEXT): Customer city (Mumbai, Delhi, Bangalore, etc.)
- state (TEXT): State
- country (TEXT): Country
- signup_date (DATE): When customer signed up
- segment (TEXT): 'Premium' / 'Regular' / 'Occasional' / 'New' / 'VIP'
- acquisition_channel (TEXT): How acquired ('Organic Search', 'Paid Ads', 'Referral', 'Social Media', 'Walk-in', 'Email Campaign')
- loyalty_points (INTEGER): Loyalty points balance
- is_active (BOOLEAN): Active status

============ TABLE 2: stores ============
Physical + online store locations.
- store_id (TEXT, PK): Unique store ID (STR001)
- store_name (TEXT): Store name (e.g., "Levi's Mumbai Flagship")
- store_type (TEXT): 'Flagship' / 'Standard' / 'Outlet' / 'Online' / 'Pop-up'
- city (TEXT): Store city
- state (TEXT): State
- country (TEXT): Country
- region (TEXT): 'North', 'South', 'East', 'West', 'Central', 'Online', 'Middle East', 'Asia'
- opening_date (DATE): When store opened
- store_manager (TEXT): Manager name
- is_active (BOOLEAN): Active status

============ TABLE 3: products ============
Product catalog (jeans, shirts, jackets, accessories, footwear, kids).
- product_id (TEXT, PK): Unique product ID (PROD00001)
- product_name (TEXT): Product name (e.g., "501 Original Fit", "Trucker Jacket")
- category (TEXT): 'Jeans' / 'Shirts' / 'Jackets' / 'Accessories' / 'Footwear' / 'Kids'
- sub_category (TEXT): More specific category
- sku (TEXT, UNIQUE): SKU code
- size (TEXT): '28', '30', '32', '34', 'S', 'M', 'L', 'XL', 'Free Size', etc.
- color (TEXT): Color
- price (NUMERIC): Selling price in INR
- cost (NUMERIC): Cost price in INR
- launch_date (DATE): Product launch date
- is_active (BOOLEAN): Active status

============ TABLE 4: campaigns ============
Marketing campaigns.
- campaign_id (TEXT, PK): Unique campaign ID (CAMP001)
- campaign_name (TEXT): Campaign name (e.g., "Diwali Bonanza 2025")
- campaign_type (TEXT): 'Seasonal' / 'Festival' / 'Brand' / 'Product Launch' / 'Discount' / 'Loyalty' / 'Acquisition' / 'Referral' / 'Digital' / 'Social Media'
- start_date (DATE): Campaign start
- end_date (DATE): Campaign end
- budget (NUMERIC): Campaign budget
- discount_percentage (NUMERIC): Discount %
- target_segment (TEXT): Target customer segment
- channel (TEXT): 'Email' / 'SMS' / 'Social Media' / 'In-Store' / 'Online'

============ TABLE 5: orders ============
Order transactions.
- order_id (TEXT, PK): Unique order ID (ORD000001)
- customer_id (TEXT, FK → customers): Customer who placed order
- store_id (TEXT, FK → stores): Store where order placed
- campaign_id (TEXT, FK → campaigns): Campaign used (NULL if none)
- order_date (TIMESTAMP): When order was placed
- delivery_date (TIMESTAMP): When delivered (NULL if not delivered)
- status (TEXT): 'DELIVERED' / 'SHIPPED' / 'CANCELLED' / 'PENDING' / 'RETURNED'
- payment_method (TEXT): 'Card' / 'UPI' / 'Cash' / 'Net Banking' / 'Wallet' / 'EMI'
- total_amount (NUMERIC): Total order value (INR, after discount + tax + shipping)
- discount_amount (NUMERIC): Discount applied
- tax_amount (NUMERIC): GST/tax
- shipping_charge (NUMERIC): Shipping cost
- is_online (BOOLEAN): Online order or store

============ TABLE 6: order_items ============
Line items per order (one row per product in an order).
- item_id (SERIAL, PK): Auto-incremented item ID
- order_id (TEXT, FK → orders): Parent order
- product_id (TEXT, FK → products): Product purchased
- quantity (INTEGER): Quantity bought
- unit_price (NUMERIC): Price per unit at time of order
- discount_per_item (NUMERIC): Discount per item
- line_total (NUMERIC): Total for this line ((unit_price - discount) × quantity)

============ KEY JOINS ============
- customers ↔ orders: ON customers.customer_id = orders.customer_id
- stores ↔ orders: ON stores.store_id = orders.store_id
- campaigns ↔ orders: ON campaigns.campaign_id = orders.campaign_id
- orders ↔ order_items: ON orders.order_id = order_items.order_id
- products ↔ order_items: ON products.product_id = order_items.product_id

============ BUSINESS RULES (very important) ============
1. "delivered orders" = WHERE orders.status = 'DELIVERED'
2. "revenue" / "sales" = SUM(orders.total_amount) WHERE status = 'DELIVERED'
3. "GMV" = SUM(orders.total_amount) (all statuses except CANCELLED)
4. "AOV" / "average order value" = AVG(orders.total_amount) WHERE status = 'DELIVERED'
5. "today" = DATE(order_date) = CURRENT_DATE
6. "this month" = order_date >= DATE_TRUNC('month', CURRENT_DATE)
7. "last month" = order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                   AND order_date < DATE_TRUNC('month', CURRENT_DATE)
8. "this year" / "YTD" = order_date >= DATE_TRUNC('year', CURRENT_DATE)
9. "last year" = EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
10. "top customer" = customer with highest SUM(total_amount) WHERE status='DELIVERED'
11. "active customers" = customers.is_active = TRUE
12. "VIP customers" = customers.segment = 'VIP'
13. "online orders" = orders.is_online = TRUE
14. "in-store orders" = orders.is_online = FALSE
15. "best-selling product" = product with highest SUM(quantity) from order_items
16. Cancelled orders (status='CANCELLED') excluded from revenue
17. Returned orders (status='RETURNED') usually counted in revenue but mention if relevant

============ COMMON HINGLISH/HINDI TERMS ============
- "kitne" / "kitna" = how many / how much
- "kaha" / "konsi" = where / which
- "sab" / "saare" = all
- "pichle mahine" = last month
- "is hafte" = this week
- "aaj" = today
- "kal" = yesterday
- "sabse zyada" = highest / most
- "sabse kam" = lowest / least
- "compare karo" = compare
- "dikhao" = show / display
- "batao" = tell
- "kharidaari" = purchase
- "graahak" = customer
- "bikri" = sales

============ RULES FOR SQL GENERATION ============
1. ONLY generate SELECT queries — NEVER INSERT, UPDATE, DELETE, DROP, ALTER
2. Always add LIMIT 1000 unless top N is asked or single aggregate
3. Use proper JOINs when multiple tables needed
4. Use table aliases: customers c, orders o, order_items oi, products p, stores s, campaigns ca
5. Use lowercase SQL keywords
6. Add ORDER BY for ranking questions
7. For "trend", "month-wise", "by month" → use DATE_TRUNC('month', order_date)
8. For "weekly trend" → use DATE_TRUNC('week', order_date)
9. For "daily trend" → use DATE_TRUNC('day', order_date)
10. For category/product analysis → JOIN orders + order_items + products
11. For customer demographics → JOIN customers + orders
12. For store performance → JOIN stores + orders
13. For campaign ROI → JOIN campaigns + orders
14. Return ONLY the SQL query — no explanation, no markdown, no comments
15. Do NOT wrap SQL in ```sql ``` markdown blocks

============ CONVERSATION CONTEXT ============
If conversation context provided:
- Use it to resolve "us city ka", "wahi data", "phir se", "iska breakdown"
- Maintain time period from previous question unless changed
- "Aur Delhi ka batao" after Mumbai query = same metric, Delhi instead

============ EXAMPLES ============

Q: "Total revenue this month"
SQL: select sum(total_amount) as revenue from orders where status='DELIVERED' and order_date >= date_trunc('month', current_date);

Q: "Top 5 cities by revenue"
SQL: select c.city, sum(o.total_amount) as revenue from customers c join orders o on c.customer_id=o.customer_id where o.status='DELIVERED' group by c.city order by revenue desc limit 5;

Q: "Best selling products"
SQL: select p.product_name, p.category, sum(oi.quantity) as units_sold, sum(oi.line_total) as revenue from products p join order_items oi on p.product_id=oi.product_id join orders o on oi.order_id=o.order_id where o.status='DELIVERED' group by p.product_name, p.category order by units_sold desc limit 10;

Q: "Monthly revenue trend this year"
SQL: select date_trunc('month', order_date) as month, sum(total_amount) as revenue from orders where status='DELIVERED' and order_date >= date_trunc('year', current_date) group by month order by month;

Q: "VIP customers ka spending"
SQL: select c.first_name || ' ' || c.last_name as customer_name, sum(o.total_amount) as total_spent from customers c join orders o on c.customer_id=o.customer_id where c.segment='VIP' and o.status='DELIVERED' group by c.customer_id, c.first_name, c.last_name order by total_spent desc limit 100;

Q: "Campaign-wise revenue"
SQL: select ca.campaign_name, ca.campaign_type, count(distinct o.order_id) as orders, sum(o.total_amount) as revenue from campaigns ca left join orders o on ca.campaign_id=o.campaign_id and o.status='DELIVERED' group by ca.campaign_id, ca.campaign_name, ca.campaign_type order by revenue desc nulls last limit 20;
"""


def generate_sql(question: str) -> tuple[str, str]:
    """Generate SQL from natural language question."""
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    prompt = f"""{SCHEMA_CONTEXT}

USER QUESTION: {question}

Generate the SQL query now (ONLY SQL, no explanation):"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a PostgreSQL expert specializing in CRM analytics. Generate only valid SELECT queries with proper JOINs."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=800
    )
    
    sql = response.choices[0].message.content.strip()
    sql = sql.replace('```sql', '').replace('```', '').strip()
    
    if sql.startswith('"') and sql.endswith('"'):
        sql = sql[1:-1]
    
    if not sql.endswith(';'):
        sql += ';'
    
    return sql, ""


def calculate_confidence(question: str, sql: str) -> int:
    """Calculate confidence score."""
    score = 70
    
    sql_lower = sql.lower()
    question_lower = question.lower()
    
    # Positive signals
    if 'limit' in sql_lower:
        score += 5
    if 'where' in sql_lower:
        score += 5
    
    # JOIN handling — proper JOINs are good for CRM
    join_count = sql_lower.count('join')
    if join_count == 1 or join_count == 2:
        score += 10  # Expected for CRM
    elif join_count > 4:
        score -= 10  # Too complex
    
    # Known schema terms
    schema_terms = ['customer', 'order', 'product', 'store', 'campaign',
                    'mumbai', 'delhi', 'jeans', 'jacket', 'vip', 'premium',
                    'revenue', 'sales', 'segment', 'category']
    matches = sum(1 for term in schema_terms if term in question_lower)
    score += min(15, matches * 2)
    
    # Negative signals
    if sql_lower.count('select') > 2:
        score -= 10
    if len(sql) < 30:
        score -= 20
    
    vague_terms = ['interesting', 'something', 'anything', 'analyze everything']
    if any(term in question_lower for term in vague_terms):
        score -= 15
    
    return max(0, min(100, score))
