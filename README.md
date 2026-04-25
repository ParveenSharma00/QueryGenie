# 📊 DataChat v3 — Levi's CRM Edition + Charts

**Major upgrade with realistic CRM data + auto-generated charts!**

---

## 🆕 What's New in v3

| Feature | v2 | v3 |
|---------|----|----|
| **Database** | 1 table (orders) | 🎯 **6 tables (full CRM)** |
| **JOINs** | ❌ None | ✅ **Multi-table joins** |
| **Charts** | ❌ Tables only | 📊 **Auto-generated charts** |
| **Sample data** | 5K rows | **~50K rows across 6 tables** |
| **Use cases** | Simple queries | **Full business analytics** |

---

## 🗃️ Database Schema (Levi's CRM)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  customers   │◄──┐   │   products   │   ┌──►│    stores    │
│  (2,000)     │   │   │   (~80)      │   │   │   (25)       │
└──────────────┘   │   └──────────────┘   │   └──────────────┘
                   │          ▲           │
                   │          │           │
                   │   ┌──────────────┐   │
                   │   │ order_items  │   │
                   │   │ (~30,000)    │   │
                   │   └──────────────┘   │
                   │          ▲           │
                   │          │           │
                   │   ┌──────────────┐   │
                   └──►│    orders    │◄──┘
                       │   (15,000)   │
                       └──────────────┘
                              ▲
                              │
                       ┌──────────────┐
                       │  campaigns   │
                       │   (30)       │
                       └──────────────┘
```

### **6 Tables:**

1. **`customers`** — Master data (segment, city, signup, loyalty)
2. **`stores`** — Physical + online stores (Flagship/Standard/Outlet/Online/Pop-up)
3. **`products`** — Catalog (Jeans, Shirts, Jackets, Accessories, Footwear, Kids)
4. **`campaigns`** — Marketing campaigns (Festival, Seasonal, Brand, etc.)
5. **`orders`** — Order transactions
6. **`order_items`** — Line items per order (for product-level analytics)

---

## 📊 Chart Support

Just add **"chart", "graph", "trend", or "dikhao"** in your question:

| Question | Auto-detected chart |
|----------|---------------------|
| "Monthly revenue trend" | 📈 Line chart |
| "Top 10 products bar graph" | 📊 Bar chart |
| "Customer segment pie chart" | 🥧 Pie chart |
| "Top cities horizontal bar" | 📏 Horizontal bar |
| "Daily orders trend chart" | 📈 Line chart |

**Charts use Plotly** — interactive, zoomable, downloadable as PNG!

---

## 🚀 Setup (Same DB, Same Groq)

### **If upgrading from v2:**

```bash
# 1. Navigate to v3 folder
cd /Users/parveenkumarsharma/Documents/text-to-sql-bot-v3

# 2. Copy .env from v2 (same Groq key, same DB)
cp ../text-to-sql-bot-v2/.env .

# 3. Activate venv (or create new one)
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies (now includes plotly)
pip install -r requirements.txt

# 5. ⚠️ IMPORTANT: Reset database with new CRM schema
python setup_data.py

# 6. Verify
python test_setup.py

# 7. Run!
streamlit run app.py
```

### **First time setup:**

Same as above, but use a fresh Supabase project for best results.

---

## ⚠️ Important: Database Reset

`setup_data.py` will:
- ❌ **Drop existing `orders` table** (from v1/v2)
- ✅ Create 6 new CRM tables
- ✅ Insert ~50,000 rows of realistic data

**Backup karna hai?** Pehle Supabase dashboard mein old `orders` table export kar lo CSV mein.

---

## 💡 Sample Queries to Try

### **🟢 Simple (single table)**

```
Total revenue this year
How many active customers?
Top 10 customers by spend
```

### **🟡 With JOINs**

```
VIP customers ka favorite product category
Online vs in-store revenue comparison
Top 5 stores by revenue
Premium segment ka average order value
```

### **📊 With Charts**

```
Monthly revenue trend chart dikhao
Top 10 products bar graph mein
Customer segment ka pie chart
Category-wise sales bar chart
Daily orders trend chart last 30 days
Store type wise revenue graph
```

### **🧠 Multi-step (Agent runs multiple SQLs)**

```
Top 3 cities ka revenue aur unme top product
Best campaign aur usse jude top customers
Top 5 products ka monthly trend chart mein
```

### **💬 Conversational follow-ups**

```
You: "Top 5 cities by revenue"
Bot: [shows top 5]
You: "Mumbai ka monthly trend dikhao chart mein"
Bot: [knows context, shows Mumbai monthly trend with chart]
You: "Wahan top customers kaun the"
Bot: [Mumbai customers]
You: "Inka product category breakdown"
Bot: [drill down further]
```

### **🇮🇳 Hinglish**

```
Pichle mahine kitne new customers signup hue?
Sabse zyada bikne wale jeans konse hain?
Mumbai store ki sales last 6 months ka trend chart mein
VIP customers ka acquisition channel breakdown pie chart
```

---

## 📁 Files in v3

| File | Status | Purpose |
|------|--------|---------|
| `app.py` | 🔄 Updated | Main UI with chart toggle |
| `agent.py` | 🔄 Updated | ReAct agent (CRM-aware) |
| **`charts.py`** | 🆕 **NEW** | Chart detection + generation |
| `sql_generator.py` | 🔄 Updated | Full 6-table schema |
| `executor.py` | ✅ Same | SQL execution |
| `utils.py` | 🔄 Updated | CRM-specific helpers |
| **`setup_data.py`** | 🔄 **NEW data** | Levi's CRM data generator |
| `test_setup.py` | 🔄 Updated | Tests all 6 tables |
| `requirements.txt` | 🔄 Updated | + plotly |
| `.env.example` | ✅ Same | Config template |
| `README.md` | This file | Documentation |

---

## 🛠️ Common Use Cases (Real Business Questions)

### **Sales & Revenue**
- Total revenue YTD vs last year
- Monthly revenue trend
- Revenue by city / region / store
- Top revenue contributors (customers / products / cities)

### **Customer Analytics**
- Customer segments distribution
- VIP customer behavior
- Customer acquisition channels
- New vs returning customers
- Customer lifetime value

### **Product Performance**
- Best selling products
- Category-wise sales
- Product mix per region
- Slow-moving inventory
- Color/size preferences

### **Store Performance**
- Top performing stores
- Online vs offline sales
- Store type comparison
- Regional analysis

### **Campaign Effectiveness**
- Campaign-wise revenue
- ROI by campaign type
- Discount effectiveness
- Channel performance

### **Operational**
- Order status distribution
- Delivery times
- Cancellation rates
- Payment method preferences

---

## 🐛 Troubleshooting

### "Module not found: plotly"
```bash
pip install plotly
```

### "Tables not found"
```bash
python setup_data.py
```

### Old `orders` table still showing
```bash
# In Supabase SQL editor:
DROP TABLE IF EXISTS orders CASCADE;
# Then re-run:
python setup_data.py
```

### Charts not appearing
- Make sure question has chart keywords: "chart", "graph", "trend", "dikhao"
- Or click "📊 Show chart" button below the data

### Multi-step queries timing out
- Break into separate questions
- Simplify the ask

---

## 📊 Performance Expectations

| Query type | Latency | Accuracy |
|-----------|---------|----------|
| Simple aggregation | 5-10 sec | 90%+ |
| Single JOIN | 8-15 sec | 85%+ |
| Multi-JOIN (3+ tables) | 12-20 sec | 75-85% |
| Multi-step reasoning | 15-30 sec | 70-80% |
| Chart generation | +1-2 sec | 95%+ |

**Cost: Still ₹0/month** (Groq free tier).

---

## 🎯 What This Demonstrates

This v3 is **portfolio-grade**:

✅ Multi-table CRM database with FK relationships  
✅ Complex JOINs handled by AI  
✅ ReAct agent for multi-step reasoning  
✅ Auto-generated interactive charts  
✅ Conversational UI with memory  
✅ Production-ready safety checks  
✅ Industry-relevant use case (retail/CRM)

**Resume update:**
> *"Built conversational AI data analyst for retail CRM (6 tables, 50K+ rows). Multi-step reasoning agent runs JOINs and combines results. Auto-generates charts (line/bar/pie) on demand. ChatGPT-style UX in Hinglish/English. ₹0 infrastructure cost."*

---

## 🚀 Next Steps

After v3 working:

1. **Real customer data** — Replace sample data with actual company data
2. **Persistent chat history** — Save conversations to DB
3. **User authentication** — Multi-user support
4. **Verified query library** — Pre-tested queries for 100% accuracy
5. **Scheduled reports** — Daily/weekly auto-emails
6. **WhatsApp integration** — Query via WhatsApp

---

**Built with ❤️ by Parveen Sharma**  
**Version:** 3.0 — CRM + Charts  
**Cost:** ₹0/month (still!)  
**Capability:** 5x v1 in same time
