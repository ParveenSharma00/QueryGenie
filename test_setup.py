"""Setup verification for v3 — checks all 6 tables."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")


def test_python_version():
    print_header("TEST 1: Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print_success("Python version OK (3.10+)")
        return True
    else:
        print_error(f"Python 3.10+ required, you have {version.major}.{version.minor}")
        return False


def test_env_file():
    print_header("TEST 2: Environment Variables")
    
    if not os.path.exists('.env'):
        print_error(".env file not found!")
        return False
    
    print_success(".env file found")
    
    groq_key = os.getenv('GROQ_API_KEY')
    db_url = os.getenv('DB_URL')
    
    if not groq_key or 'your_groq' in groq_key:
        print_error("GROQ_API_KEY not set properly")
        return False
    print_success(f"GROQ_API_KEY set ({groq_key[:15]}...)")
    
    if not db_url or 'your_password' in db_url:
        print_error("DB_URL not set properly")
        return False
    print_success(f"DB_URL set ({db_url[:40]}...)")
    
    return True


def test_dependencies():
    print_header("TEST 3: Python Dependencies")
    
    required = ['streamlit', 'groq', 'psycopg2', 'pandas', 'openpyxl', 'dotenv', 'plotly']
    missing = []
    
    for pkg in required:
        try:
            if pkg == 'dotenv':
                __import__('dotenv')
            elif pkg == 'psycopg2':
                __import__('psycopg2')
            else:
                __import__(pkg)
            print_success(f"{pkg} installed")
        except ImportError:
            print_error(f"{pkg} NOT installed")
            missing.append(pkg)
    
    if missing:
        print_warning("Run: pip install -r requirements.txt")
        return False
    return True


def test_database_connection():
    print_header("TEST 4: Database Connection")
    
    try:
        import psycopg2
        db_url = os.getenv('DB_URL')
        
        print("Connecting to Supabase...")
        conn = psycopg2.connect(db_url, connect_timeout=10)
        
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print_success("Connected!")
            print(f"   Postgres: {version[:50]}...")
        
        conn.close()
        return True
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False


def test_crm_tables():
    """Check all 6 CRM tables exist with data."""
    print_header("TEST 5: CRM Tables (6 tables)")
    
    expected_tables = ['customers', 'stores', 'products', 'campaigns', 'orders', 'order_items']
    
    try:
        import psycopg2
        conn = psycopg2.connect(os.getenv('DB_URL'))
        
        all_good = True
        
        with conn.cursor() as cur:
            for table in expected_tables:
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """)
                exists = cur.fetchone()[0]
                
                if not exists:
                    print_error(f"Table '{table}' not found")
                    all_good = False
                    continue
                
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                
                if count == 0:
                    print_warning(f"Table '{table}' is empty")
                    all_good = False
                else:
                    print_success(f"{table}: {count:,} rows")
        
        conn.close()
        
        if not all_good:
            print_warning("Run: python setup_data.py")
        
        return all_good
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        return False


def test_groq_api():
    print_header("TEST 6: Groq LLM API")
    
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        print("Calling Groq API...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Reply with: WORKING"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print_success(f"Groq API works! Response: {result}")
        return True
    except Exception as e:
        print_error(f"Groq API failed: {str(e)}")
        return False


def test_full_pipeline():
    """E2E test with JOIN query."""
    print_header("TEST 7: Full Pipeline (E2E with JOIN)")
    
    try:
        from sql_generator import generate_sql
        from executor import execute_sql
        
        question = "Top 3 cities by revenue"
        print(f"Question: '{question}'")
        
        print("Generating SQL (with JOIN)...")
        sql, _ = generate_sql(question)
        print(f"   SQL: {sql[:200]}...")
        
        print("Executing...")
        df, status = execute_sql(sql)
        
        if df is None:
            print_error(f"Execution failed: {status}")
            return False
        
        print_success(f"Pipeline works! Got {len(df)} rows")
        print(f"   Sample:\n{df.head(3).to_string(index=False)}")
        return True
    except Exception as e:
        print_error(f"Pipeline failed: {str(e)}")
        return False


def main():
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║  DataChat v3 — Levi's CRM Setup Verification            ║{RESET}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════╝{RESET}")
    
    tests = [
        ("Python Version", test_python_version),
        ("Environment Variables", test_env_file),
        ("Dependencies", test_dependencies),
        ("Database Connection", test_database_connection),
        ("CRM Tables", test_crm_tables),
        ("Groq API", test_groq_api),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((name, False))
    
    print_header("FINAL SUMMARY")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {status}  {name}")
    
    print(f"\n  {passed}/{total} tests passed\n")
    
    if passed == total:
        print(f"{GREEN}🎉 All systems GO! Run: streamlit run app.py{RESET}\n")
    else:
        print(f"{YELLOW}⚠️  Fix the failed tests before running the app.{RESET}\n")


if __name__ == "__main__":
    main()
