"""
ReAct Agent v3 — Multi-step reasoning + Chart awareness
"""

import os
import json
from groq import Groq
from typing import Optional
import pandas as pd

from sql_generator import generate_sql, SCHEMA_CONTEXT
from executor import execute_sql

# ==================== CONFIG ====================
MAX_STEPS = 5
HISTORY_LIMIT = 10

# ==================== AGENT PROMPTS ====================

PLANNER_PROMPT = """You are a data analyst AI agent for Levi's CRM database (6 tables: customers, products, stores, orders, order_items, campaigns).

DATABASE SCHEMA SUMMARY:
{schema_summary}

CONVERSATION HISTORY (recent):
{history}

LAST QUERY RESULT (if any):
{last_result}

USER'S CURRENT QUESTION:
{question}

INSTRUCTIONS:
1. Analyze if this is a follow-up to previous question (use context)
2. Decide approach:
   - Single SQL query (most common)
   - Multiple SQL queries (decompose for complex questions)
   - Use previous result (no new query needed)
3. For complex questions, break into 2-3 sub-questions max
4. If question is unclear, ask for clarification

RESPOND IN VALID JSON ONLY (no markdown, no explanation):
{{
    "thinking": "Your reasoning",
    "needs_clarification": false,
    "clarification_question": null,
    "uses_previous_result": false,
    "sub_questions": ["sub-question 1", "sub-question 2"],
    "final_answer_template": "How to combine results"
}}

EXAMPLES:

Q: "Top 5 cities ka revenue chart dikhao"
{{
    "thinking": "User wants top 5 cities by revenue. Single SQL with JOIN customers+orders. Chart will be auto-detected.",
    "needs_clarification": false,
    "uses_previous_result": false,
    "sub_questions": ["Top 5 cities by total revenue"],
    "final_answer_template": "Show top 5 cities with revenue + chart"
}}

Q: "Aur monthly trend dikhao iska"  (after city query)
{{
    "thinking": "Follow-up — wants monthly trend of those top 5 cities. Need new SQL with time grouping.",
    "needs_clarification": false,
    "uses_previous_result": false,
    "sub_questions": ["Monthly revenue trend for top 5 cities last year"],
    "final_answer_template": "Show monthly trend with line chart"
}}

Q: "VIP customers ka favorite product category"
{{
    "thinking": "Need JOIN customers+orders+order_items+products. Filter by segment=VIP, group by category, count quantities.",
    "needs_clarification": false,
    "uses_previous_result": false,
    "sub_questions": ["Product categories ranked by VIP customer purchases"],
    "final_answer_template": "Show categories with VIP purchase counts"
}}

Q: "Top 3 products aur unka monthly trend"
{{
    "thinking": "Two-step: first find top 3 products, then monthly trend for those products.",
    "needs_clarification": false,
    "uses_previous_result": false,
    "sub_questions": [
        "Top 3 best-selling products by quantity",
        "Monthly sales trend for top 3 products"
    ],
    "final_answer_template": "Combine: top products list + their monthly trends"
}}

NOW RESPOND FOR USER'S QUESTION (JSON only):
"""


ANSWER_FORMATTER_PROMPT = """You are a data analyst summarizing query results for a business user.

USER'S QUESTION: {question}

DATA RESULTS:
{results}

PREVIOUS CONVERSATION:
{history}

Format a clear, concise answer:
- Match user's language style (English/Hinglish)
- Use specific numbers
- Use ₹ for revenue, format large numbers (₹1.2 Cr, ₹45.6 L, ₹12,345)
- Highlight key insights
- 2-4 sentences for simple, 4-6 for complex
- Don't repeat data already in the table

Just respond with answer text — no JSON, no markdown headers."""


SCHEMA_SUMMARY = """
6 tables for Levi's CRM:
- customers (id, name, city, segment[VIP/Premium/Regular/Occasional/New], gender, signup_date)
- stores (id, name, type[Flagship/Standard/Outlet/Online/Pop-up], city, region)
- products (id, name, category[Jeans/Shirts/Jackets/Accessories/Footwear/Kids], price, color, size)
- campaigns (id, name, type, start/end date, discount %)
- orders (id, customer_id, store_id, campaign_id, order_date, status[DELIVERED/SHIPPED/CANCELLED/PENDING/RETURNED], total_amount, payment_method)
- order_items (order_id, product_id, quantity, unit_price, line_total)

Common JOINs:
- Revenue by city: customers c JOIN orders o
- Product analysis: products p JOIN order_items oi JOIN orders o
- Store performance: stores s JOIN orders o
- Campaign ROI: campaigns ca JOIN orders o
"""


# ==================== HELPERS ====================

def get_groq_client():
    return Groq(api_key=os.getenv('GROQ_API_KEY'))


def format_history(messages: list, limit: int = HISTORY_LIMIT) -> str:
    if not messages:
        return "No previous conversation."
    
    recent = messages[-limit:]
    formatted = []
    for msg in recent:
        role = msg["role"].upper()
        content = msg["content"][:200]
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted)


def format_dataframe_for_context(df: Optional[pd.DataFrame], max_rows: int = 10) -> str:
    if df is None or df.empty:
        return "No previous data."
    
    summary = f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
    summary += f"Columns: {', '.join(df.columns.tolist())}\n\n"
    summary += "Sample:\n"
    summary += df.head(max_rows).to_string(index=False)
    
    if len(df) > max_rows:
        summary += f"\n... ({len(df) - max_rows} more rows)"
    
    return summary


def parse_json_response(text: str) -> dict:
    text = text.strip()
    
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    
    text = text.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        # Fallback default
        return {
            "thinking": "Defaulting to single query",
            "needs_clarification": False,
            "uses_previous_result": False,
            "sub_questions": [text[:200]],
            "final_answer_template": ""
        }


# ==================== AGENT TOOLS ====================

def plan_steps(question: str, history: list, last_df: Optional[pd.DataFrame]) -> dict:
    client = get_groq_client()
    
    prompt = PLANNER_PROMPT.format(
        schema_summary=SCHEMA_SUMMARY,
        history=format_history(history),
        last_result=format_dataframe_for_context(last_df),
        question=question
    )
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a planning agent. Always respond in valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=800
    )
    
    content = response.choices[0].message.content
    return parse_json_response(content)


def execute_sub_question(sub_question: str, history: list) -> tuple[Optional[pd.DataFrame], str, str]:
    """Execute a sub-question."""
    try:
        # Add context if needed
        context_hint = ""
        if history:
            recent = history[-4:]
            context_hint = "\n\nCONVERSATION CONTEXT:\n"
            for msg in recent:
                context_hint += f"{msg['role']}: {msg['content'][:100]}\n"
        
        enhanced_question = sub_question + context_hint
        sql, _ = generate_sql(enhanced_question)
        df, status = execute_sql(sql)
        
        return df, sql, status
    
    except Exception as e:
        return None, "", f"Error: {str(e)}"


def format_final_answer(question: str, results: list, history: list) -> str:
    client = get_groq_client()
    
    results_text = ""
    for i, (sub_q, df, sql) in enumerate(results, 1):
        results_text += f"\n--- Result {i} (for: {sub_q}) ---\n"
        if df is not None and not df.empty:
            results_text += df.head(20).to_string(index=False)
            if len(df) > 20:
                results_text += f"\n... ({len(df) - 20} more rows)"
        else:
            results_text += "No data returned"
    
    prompt = ANSWER_FORMATTER_PROMPT.format(
        question=question,
        results=results_text,
        history=format_history(history, limit=4)
    )
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a data analyst. Give clear, concise answers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    return response.choices[0].message.content.strip()


def combine_dataframes(results: list) -> Optional[pd.DataFrame]:
    """Combine multiple DataFrames intelligently."""
    valid_dfs = [(sq, df, sql) for sq, df, sql in results if df is not None and not df.empty]
    
    if not valid_dfs:
        return None
    
    if len(valid_dfs) == 1:
        return valid_dfs[0][1]
    
    # Try to concatenate if same columns
    first_cols = set(valid_dfs[0][1].columns)
    if all(set(df.columns) == first_cols for _, df, _ in valid_dfs):
        try:
            return pd.concat([df for _, df, _ in valid_dfs], ignore_index=True)
        except:
            pass
    
    # Return largest
    return max(valid_dfs, key=lambda x: len(x[1]))[1]


# ==================== MAIN AGENT LOOP ====================

def react_agent(
    question: str,
    conversation_history: list = None,
    last_df: Optional[pd.DataFrame] = None,
    progress_callback=None
) -> dict:
    """
    ReAct agent main loop.
    
    Returns:
        {
            "answer": str,
            "data": DataFrame|None,
            "steps": list,
            "success": bool
        }
    """
    if conversation_history is None:
        conversation_history = []
    
    steps = []
    
    def log_progress(msg):
        if progress_callback:
            progress_callback(msg)
    
    try:
        # STEP 1: PLAN
        log_progress("Planning approach...")
        plan = plan_steps(question, conversation_history, last_df)
        
        steps.append({
            "thought": plan.get("thinking", ""),
            "type": "planning"
        })
        
        if plan.get("needs_clarification"):
            return {
                "answer": plan.get("clarification_question", "Could you clarify your question?"),
                "data": None,
                "steps": steps,
                "success": True
            }
        
        # STEP 2: EXECUTE
        sub_questions = plan.get("sub_questions", [])
        if not sub_questions:
            sub_questions = [question]
        
        results = []
        
        for i, sub_q in enumerate(sub_questions, 1):
            log_progress(f"Running query {i}/{len(sub_questions)}...")
            
            df, sql, status = execute_sub_question(sub_q, conversation_history)
            
            step_data = {
                "thought": f"Sub-question {i}: {sub_q}",
                "type": "query",
                "sql": sql
            }
            
            if df is not None and not df.empty:
                step_data["result_summary"] = f"Got {len(df)} rows, {len(df.columns)} columns"
            else:
                step_data["result_summary"] = f"No data: {status}"
            
            steps.append(step_data)
            results.append((sub_q, df, sql))
        
        # STEP 3: COMBINE & ANSWER
        log_progress("Formatting answer...")
        combined_df = combine_dataframes(results)
        final_answer = format_final_answer(question, results, conversation_history)
        
        steps.append({
            "thought": "Combined results, formatted answer",
            "type": "synthesis"
        })
        
        return {
            "answer": final_answer,
            "data": combined_df,
            "steps": steps,
            "success": True
        }
    
    except Exception as e:
        return {
            "answer": f"Sorry, error aa gaya: {str(e)}\n\nTry rephrasing the question.",
            "data": None,
            "steps": steps,
            "success": False
        }
