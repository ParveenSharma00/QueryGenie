"""
DataChat v3 — Conversational AI Data Analyst with Charts
- Levi's CRM data (6 tables, JOINs)
- Continuous chat (ChatGPT-style)
- Multi-step reasoning (ReAct agent)
- Auto-generated charts when requested
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

from agent import react_agent
from executor import test_connection
from charts import wants_chart, create_chart, detect_chart_type
from utils import get_sample_questions

load_dotenv()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="DataChat — Levi's AI Analyst",
    page_icon="👖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #c41e3a;
        margin-bottom: 0;
    }
    .sub-header {
        color: #666;
        font-size: 1rem;
        margin-top: 0;
    }
    .stChatMessage {
        padding: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown('<p class="main-header">👖 DataChat — Levi\'s AI Analyst</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Ask in English/Hinglish • Multi-step reasoning • Auto charts • Excel download</p>',
        unsafe_allow_html=True
    )

with col_h2:
    st.write("")
    if st.button("🆕 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_df = None
        st.session_state.query_count = 0
        st.rerun()

st.divider()

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_df" not in st.session_state:
    st.session_state.last_df = None
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "show_thinking" not in st.session_state:
    st.session_state.show_thinking = True

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **DataChat v3** — Conversational AI for Levi's CRM
    
    **Database:** 6 tables  
    👥 Customers (2K)  
    🏬 Stores (25)  
    👖 Products (80)  
    🎯 Campaigns (30)  
    📋 Orders (15K)  
    🛒 Order Items (~30K)
    
    **Try chart commands:**
    - "trend dikhao"
    - "show pie chart"
    - "bar graph banao"
    """)
    
    st.divider()
    
    # Settings
    st.header("⚙️ Settings")
    st.session_state.show_thinking = st.checkbox(
        "🔍 Show agent thinking",
        value=st.session_state.show_thinking
    )
    
    st.divider()
    
    st.header("💡 Sample Queries")
    sample_questions = get_sample_questions()
    
    selected_sample = st.selectbox(
        "Try these:",
        [""] + sample_questions,
        key="sample_select"
    )
    
    if st.button("📥 Load sample", use_container_width=True) and selected_sample:
        st.session_state.pending_question = selected_sample
        st.rerun()
    
    st.divider()
    
    st.header("📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Queries", st.session_state.query_count)
    
    st.divider()
    
    # Connection
    st.header("🔌 Connection")
    if st.button("Test DB", use_container_width=True):
        with st.spinner("Testing..."):
            ok, msg = test_connection()
            if ok:
                st.success("✅ Connected")
            else:
                st.error(f"❌ {msg}")
    
    st.divider()
    
    st.markdown("""
    ---
    **Built by:** Parveen Sharma  
    **Version:** 3.0 (CRM + Charts)  
    **Stack:** Streamlit + Groq + Supabase + Plotly
    """)

# ==================== DISPLAY HISTORY ====================
def display_message(msg, idx):
    """Display a single chat message."""
    with st.chat_message(msg["role"]):
        # Show thinking
        if msg["role"] == "assistant" and "steps" in msg and st.session_state.show_thinking:
            with st.expander("🧠 Agent thinking", expanded=False):
                for i, step in enumerate(msg["steps"], 1):
                    st.markdown(f"**Step {i}:** {step.get('thought', '')}")
                    if step.get("sql"):
                        st.code(step["sql"], language="sql")
                    if step.get("result_summary"):
                        st.caption(f"📊 {step['result_summary']}")
        
        # Main answer
        st.markdown(msg["content"])
        
        # Show data + chart if assistant message
        if msg["role"] == "assistant" and msg.get("data") is not None:
            df = pd.DataFrame(msg["data"])
            if not df.empty:
                # Show chart if applicable
                if msg.get("show_chart") and len(df) > 0:
                    chart = create_chart(df, msg.get("question", ""))
                    if chart is not None:
                        st.plotly_chart(chart, use_container_width=True, key=f"chart_{idx}")
                
                # Always show data table
                st.dataframe(df.head(50), use_container_width=True, hide_index=True)
                
                if len(df) > 50:
                    st.caption(f"Showing first 50 of {len(df)} rows")
                
                # Download buttons
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Data', index=False)
                        meta = pd.DataFrame({
                            'Field': ['Question', 'Generated On', 'Total Rows'],
                            'Value': [msg.get("question", "N/A"), 
                                     msg.get("timestamp", "N/A"), 
                                     len(df)]
                        })
                        meta.to_excel(writer, sheet_name='Query_Info', index=False)
                    
                    st.download_button(
                        "📥 Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"datachat_{idx}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"excel_{idx}",
                        use_container_width=True
                    )
                
                with col_dl2:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 CSV",
                        data=csv_data,
                        file_name=f"datachat_{idx}.csv",
                        mime="text/csv",
                        key=f"csv_{idx}",
                        use_container_width=True
                    )
                
                with col_dl3:
                    # Toggle chart
                    if st.button(
                        "📊 Toggle chart" if msg.get("show_chart") else "📊 Show chart",
                        key=f"toggle_chart_{idx}",
                        use_container_width=True
                    ):
                        st.session_state.messages[idx]["show_chart"] = not msg.get("show_chart", False)
                        st.rerun()


# Display all messages
for idx, msg in enumerate(st.session_state.messages):
    display_message(msg, idx)

# ==================== CHAT INPUT ====================
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question
else:
    user_input = st.chat_input("Ask about Levi's CRM data... (English / Hinglish, add 'chart' / 'graph' / 'trend' for visuals)")

if user_input:
    # User wants chart?
    show_chart = wants_chart(user_input)
    
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Agent response
    with st.chat_message("assistant"):
        progress_placeholder = st.empty()
        
        with progress_placeholder.container():
            st.info("🤔 Sochne do...")
        
        try:
            result = react_agent(
                question=user_input,
                conversation_history=st.session_state.messages[:-1],
                last_df=st.session_state.last_df,
                progress_callback=lambda msg: progress_placeholder.info(f"⚙️ {msg}")
            )
            
            progress_placeholder.empty()
            
            # Show thinking
            if st.session_state.show_thinking and result.get("steps"):
                with st.expander("🧠 Agent thinking", expanded=False):
                    for i, step in enumerate(result["steps"], 1):
                        st.markdown(f"**Step {i}:** {step.get('thought', '')}")
                        if step.get("sql"):
                            st.code(step["sql"], language="sql")
                        if step.get("result_summary"):
                            st.caption(f"📊 {step['result_summary']}")
            
            # Show answer
            st.markdown(result["answer"])
            
            df = result.get("data")
            if df is not None and not df.empty:
                # Show chart if requested
                if show_chart:
                    chart = create_chart(df, user_input)
                    if chart is not None:
                        st.plotly_chart(chart, use_container_width=True, key=f"chart_new_{len(st.session_state.messages)}")
                    else:
                        st.warning("⚠️ Couldn't generate chart for this data. Showing table instead.")
                
                # Always show table
                st.dataframe(df.head(50), use_container_width=True, hide_index=True)
                
                if len(df) > 50:
                    st.caption(f"Showing first 50 of {len(df)} rows")
                
                st.session_state.last_df = df
                
                # Downloads
                msg_idx = len(st.session_state.messages)
                
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Data', index=False)
                        meta = pd.DataFrame({
                            'Field': ['Question', 'Generated On', 'Total Rows'],
                            'Value': [user_input, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(df)]
                        })
                        meta.to_excel(writer, sheet_name='Query_Info', index=False)
                    
                    st.download_button(
                        "📥 Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"datachat_{msg_idx}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"excel_new_{msg_idx}",
                        use_container_width=True
                    )
                
                with col_dl2:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 CSV",
                        data=csv_data,
                        file_name=f"datachat_{msg_idx}.csv",
                        mime="text/csv",
                        key=f"csv_new_{msg_idx}",
                        use_container_width=True
                    )
                
                with col_dl3:
                    if not show_chart:
                        if st.button("📊 Show chart", key=f"toggle_new_{msg_idx}", use_container_width=True):
                            st.session_state.messages[-1]["show_chart"] = True if st.session_state.messages else False
                            st.rerun()
            
            # Save to history
            assistant_msg = {
                "role": "assistant",
                "content": result["answer"],
                "steps": result.get("steps", []),
                "question": user_input,
                "show_chart": show_chart,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if df is not None and not df.empty:
                assistant_msg["data"] = df.to_dict('records')
            
            st.session_state.messages.append(assistant_msg)
            st.session_state.query_count += 1
        
        except Exception as e:
            progress_placeholder.empty()
            error_msg = f"❌ Error: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

# ==================== EMPTY STATE ====================
if not st.session_state.messages:
    st.info("""
    👋 **Welcome to DataChat v3 — Levi's CRM Edition!**
    
    **Database has 6 tables** with realistic data: customers, products, stores, orders, items, campaigns.
    
    **Try these conversation flows:**
    
    🟢 **Simple:**
    - "Total revenue this year"
    - "Top 5 cities by sales"
    - "Best selling product category"
    
    🟡 **With JOINs:**
    - "VIP customers ka favorite product category"
    - "Online vs in-store revenue"
    - "Campaign-wise revenue analysis"
    
    📊 **With Charts:**
    - "Monthly revenue trend chart dikhao"
    - "Top 10 products bar graph mein"
    - "Customer segment ka pie chart"
    - "Store type wise revenue comparison graph"
    
    💬 **Conversational follow-ups:**
    1. "Top 5 cities by revenue"
    2. "Mumbai ka monthly trend dikhao chart mein"
    3. "Wahan top customers kaun the"
    4. "Inka product category breakdown"
    """)

st.divider()
st.caption("⚠️ Always verify critical numbers with your data team. AI can make mistakes.")
