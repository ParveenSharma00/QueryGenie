"""
SQL Executor Module
Safely executes SQL queries with validation
"""

import os
import psycopg2
import pandas as pd
import re

# ==================== SAFETY RULES ====================
DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
    'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE', 'EXEC',
    'EXECUTE', 'MERGE', 'CALL'
]

MAX_ROWS = 10000  # Hard limit on rows returned
QUERY_TIMEOUT = 30  # Seconds


def is_safe_sql(sql: str) -> tuple[bool, str]:
    """
    Validate SQL is safe to execute.
    
    Returns:
        tuple: (is_safe, message)
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query"
    
    sql_clean = sql.strip().upper()
    
    # Must start with SELECT
    if not sql_clean.startswith('SELECT') and not sql_clean.startswith('WITH'):
        return False, "Only SELECT queries are allowed"
    
    # Check for dangerous keywords (using word boundaries)
    for keyword in DANGEROUS_KEYWORDS:
        # Use regex word boundary to avoid false positives like "DELETED"
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_clean):
            return False, f"Forbidden keyword detected: {keyword}"
    
    # Block multiple statements (SQL injection prevention)
    # Remove the trailing semicolon first, then check
    sql_no_trailing = sql.rstrip().rstrip(';').strip()
    if ';' in sql_no_trailing:
        return False, "Multiple statements not allowed"
    
    # Block comments (often used for injection)
    if '--' in sql or '/*' in sql:
        return False, "SQL comments not allowed"
    
    return True, "OK"


def execute_sql(sql: str) -> tuple[pd.DataFrame, str]:
    """
    Execute SQL and return results as DataFrame.
    
    Returns:
        tuple: (dataframe_or_none, status_message)
    """
    # Safety check first
    safe, msg = is_safe_sql(sql)
    if not safe:
        return None, f"Safety check failed: {msg}"
    
    db_url = os.getenv('DB_URL')
    if not db_url:
        return None, "Database URL not configured. Check .env file."
    
    conn = None
    try:
        # Connect with timeout
        conn = psycopg2.connect(db_url, connect_timeout=10)
        
        # Set query timeout (PostgreSQL specific)
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {QUERY_TIMEOUT * 1000};")
        
        # Execute query
        df = pd.read_sql(sql, conn)
        
        # Truncate if too large
        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)
            return df, f"Result truncated to {MAX_ROWS} rows"
        
        return df, "Success"
    
    except psycopg2.errors.QueryCanceled:
        return None, f"Query timeout (>{QUERY_TIMEOUT}s). Try a more specific question."
    
    except psycopg2.errors.SyntaxError as e:
        return None, f"SQL syntax error: {str(e)}"
    
    except psycopg2.errors.UndefinedTable as e:
        return None, f"Table not found: {str(e)}"
    
    except psycopg2.errors.UndefinedColumn as e:
        return None, f"Column not found: {str(e)}"
    
    except Exception as e:
        return None, f"Database error: {str(e)}"
    
    finally:
        if conn:
            conn.close()


def test_connection() -> tuple[bool, str]:
    """Test if database connection works."""
    db_url = os.getenv('DB_URL')
    if not db_url:
        return False, "DB_URL not set in .env"
    
    try:
        conn = psycopg2.connect(db_url, connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        conn.close()
        return True, "Connection successful"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
