"""
Chart Generator Module
Auto-detects when user wants visualization and creates appropriate charts.
Uses Plotly (interactive, beautiful, included in Streamlit).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


# ==================== CHART INTENT DETECTION ====================

CHART_KEYWORDS_ENGLISH = [
    'chart', 'graph', 'plot', 'visualize', 'visualisation', 'visualization',
    'show graph', 'show chart', 'draw', 'display chart',
    'trend', 'trends', 'over time', 'timeline',
    'bar chart', 'line chart', 'pie chart', 'pie', 'bar graph',
    'distribution', 'breakdown chart',
    'compare visually', 'visual comparison'
]

CHART_KEYWORDS_HINGLISH = [
    'graph dikhao', 'chart dikhao', 'graph banao', 'chart banao',
    'visually dikhao', 'visualize karo', 'plot karo',
    'trend dikhao', 'trend chart', 'pie chart dikhao',
    'bar chart', 'line graph', 'graph mein dikhao',
    'chart mein dikhao', 'visualization karo'
]


def wants_chart(question: str) -> bool:
    """Detect if user wants a chart/visualization."""
    q_lower = question.lower()
    
    for keyword in CHART_KEYWORDS_ENGLISH + CHART_KEYWORDS_HINGLISH:
        if keyword in q_lower:
            return True
    
    return False


def detect_chart_type(question: str, df: pd.DataFrame) -> str:
    """
    Auto-detect best chart type based on question + data shape.
    Returns: 'line', 'bar', 'pie', 'scatter', 'horizontal_bar', 'area'
    """
    q_lower = question.lower()
    
    # Explicit user preference
    if 'pie' in q_lower:
        return 'pie'
    if 'line' in q_lower or 'trend' in q_lower or 'over time' in q_lower or 'timeline' in q_lower:
        return 'line'
    if 'horizontal bar' in q_lower:
        return 'horizontal_bar'
    if 'scatter' in q_lower:
        return 'scatter'
    if 'area' in q_lower:
        return 'area'
    if 'bar' in q_lower:
        return 'bar'
    
    # Auto-detect based on data
    if df.empty:
        return 'bar'
    
    # Check if first column is date/time
    first_col = df.columns[0]
    if pd.api.types.is_datetime64_any_dtype(df[first_col]):
        return 'line'  # Time series → line chart
    
    # Try to parse as date
    try:
        pd.to_datetime(df[first_col].iloc[0])
        # If dates present and many rows → line chart
        if len(df) > 5:
            return 'line'
    except:
        pass
    
    # Time-related keywords in question → line chart
    time_words = ['month', 'week', 'day', 'year', 'quarter', 'mahine', 'hafte', 'daily', 'monthly']
    if any(w in q_lower for w in time_words):
        return 'line'
    
    # Distribution / share → pie chart
    distribution_words = ['distribution', 'share', 'percentage', 'percent', 'breakdown', 'proportion', 'split']
    if any(w in q_lower for w in distribution_words) and len(df) <= 8:
        return 'pie'
    
    # Top N → horizontal bar (better for category names)
    if 'top' in q_lower and len(df) <= 15:
        return 'horizontal_bar'
    
    # Default: vertical bar
    return 'bar'


# ==================== CHART GENERATORS ====================

def create_chart(df: pd.DataFrame, question: str, chart_type: Optional[str] = None) -> Optional[go.Figure]:
    """
    Create a chart from DataFrame.
    
    Args:
        df: DataFrame with results
        question: Original user question (for title + type detection)
        chart_type: Override auto-detection
    
    Returns:
        Plotly Figure or None
    """
    if df is None or df.empty or len(df.columns) < 2:
        return None
    
    if chart_type is None:
        chart_type = detect_chart_type(question, df)
    
    # Title from question (cleaned)
    title = generate_title(question, chart_type)
    
    # Identify x and y columns
    x_col = df.columns[0]
    y_cols = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
    
    if not y_cols:
        return None  # No numeric columns to plot
    
    y_col = y_cols[0]  # Primary metric
    
    try:
        if chart_type == 'line':
            return create_line_chart(df, x_col, y_cols, title)
        elif chart_type == 'pie':
            return create_pie_chart(df, x_col, y_col, title)
        elif chart_type == 'horizontal_bar':
            return create_horizontal_bar(df, x_col, y_col, title)
        elif chart_type == 'scatter':
            return create_scatter(df, x_col, y_col, title)
        elif chart_type == 'area':
            return create_area_chart(df, x_col, y_cols, title)
        else:  # bar
            return create_bar_chart(df, x_col, y_cols, title)
    except Exception as e:
        print(f"Chart generation error: {e}")
        return None


def create_line_chart(df, x_col, y_cols, title):
    """Line chart for trends/time series."""
    df_sorted = df.copy()
    
    # Try to convert x to datetime for proper sorting
    try:
        df_sorted[x_col] = pd.to_datetime(df_sorted[x_col])
        df_sorted = df_sorted.sort_values(x_col)
    except:
        pass
    
    fig = go.Figure()
    
    for col in y_cols[:3]:  # Max 3 lines
        fig.add_trace(go.Scatter(
            x=df_sorted[x_col],
            y=df_sorted[col],
            mode='lines+markers',
            name=col.replace('_', ' ').title(),
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title=y_cols[0].replace('_', ' ').title(),
        hovermode='x unified',
        template='plotly_white',
        height=450,
        showlegend=len(y_cols) > 1
    )
    
    return fig


def create_bar_chart(df, x_col, y_cols, title):
    """Vertical bar chart."""
    df_plot = df.head(20)  # Limit bars
    
    fig = go.Figure()
    
    for col in y_cols[:2]:  # Max 2 metrics side by side
        fig.add_trace(go.Bar(
            x=df_plot[x_col].astype(str),
            y=df_plot[col],
            name=col.replace('_', ' ').title(),
            text=df_plot[col].apply(lambda x: format_number(x)),
            textposition='outside'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title=y_cols[0].replace('_', ' ').title(),
        template='plotly_white',
        height=450,
        showlegend=len(y_cols) > 1,
        barmode='group'
    )
    
    return fig


def create_horizontal_bar(df, x_col, y_col, title):
    """Horizontal bar - good for top N rankings."""
    df_plot = df.head(15).copy()
    df_plot = df_plot.sort_values(y_col, ascending=True)
    
    fig = go.Figure(go.Bar(
        x=df_plot[y_col],
        y=df_plot[x_col].astype(str),
        orientation='h',
        text=df_plot[y_col].apply(lambda x: format_number(x)),
        textposition='outside',
        marker_color='#1f77b4'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=y_col.replace('_', ' ').title(),
        yaxis_title=x_col.replace('_', ' ').title(),
        template='plotly_white',
        height=max(400, len(df_plot) * 35)
    )
    
    return fig


def create_pie_chart(df, x_col, y_col, title):
    """Pie chart for distribution/share."""
    df_plot = df.head(8).copy()  # Max 8 slices
    
    fig = go.Figure(go.Pie(
        labels=df_plot[x_col].astype(str),
        values=df_plot[y_col],
        hole=0.4,  # Donut style
        textinfo='label+percent',
        textposition='outside'
    ))
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=450
    )
    
    return fig


def create_scatter(df, x_col, y_col, title):
    """Scatter plot for correlations."""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        title=title,
        template='plotly_white',
        height=450
    )
    
    return fig


def create_area_chart(df, x_col, y_cols, title):
    """Area chart for cumulative trends."""
    df_sorted = df.copy()
    
    try:
        df_sorted[x_col] = pd.to_datetime(df_sorted[x_col])
        df_sorted = df_sorted.sort_values(x_col)
    except:
        pass
    
    fig = go.Figure()
    
    for col in y_cols[:3]:
        fig.add_trace(go.Scatter(
            x=df_sorted[x_col],
            y=df_sorted[col],
            mode='lines',
            name=col.replace('_', ' ').title(),
            stackgroup='one',
            fill='tonexty'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title=y_cols[0].replace('_', ' ').title(),
        template='plotly_white',
        height=450
    )
    
    return fig


# ==================== HELPERS ====================

def generate_title(question: str, chart_type: str) -> str:
    """Generate chart title from question."""
    # Remove chart-related words
    q = question
    remove_words = [
        'show me', 'show the', 'show', 'display', 'create', 'make', 'draw',
        'chart', 'graph', 'plot', 'visualization', 'visualize',
        'dikhao', 'banao', 'karo', 'mein', 'me'
    ]
    
    q_clean = q.lower()
    for w in remove_words:
        q_clean = q_clean.replace(w, '')
    
    q_clean = ' '.join(q_clean.split())  # Clean whitespace
    
    if not q_clean.strip():
        q_clean = "Data Visualization"
    
    return q_clean.title()


def format_number(value) -> str:
    """Format number for display."""
    try:
        value = float(value)
        if value >= 10000000:
            return f"{value/10000000:.1f}Cr"
        elif value >= 100000:
            return f"{value/100000:.1f}L"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:.0f}"
    except:
        return str(value)
