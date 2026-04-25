"""Utility functions for DataChat v3."""

import pandas as pd


def get_sample_questions() -> list:
    """Sample questions covering all 6 tables + charts."""
    return [
        # Simple aggregations
        "Total revenue this year",
        "How many active customers do we have?",
        "Total orders this month",
        
        # Single-table
        "Top 10 customers by total spend",
        "Top 5 cities by customer count",
        "Best selling product category",
        
        # JOINs
        "VIP customers ka favorite product category",
        "Online vs in-store revenue compare karo",
        "Top 5 stores by revenue",
        "Campaign-wise revenue analysis",
        "Premium segment ka average order value",
        
        # Charts
        "Monthly revenue trend chart dikhao",
        "Top 10 products bar graph mein",
        "Customer segment ka pie chart",
        "Category-wise sales bar chart",
        "Daily orders trend last 30 days",
        "Store type wise revenue graph",
        
        # Multi-step
        "Top 3 cities ka revenue aur unme top product",
        "Best campaign aur usse jude top customers",
        "Top 5 products ka monthly trend dikhao chart mein",
        
        # Hinglish
        "Pichle mahine kitne new customers signup hue?",
        "Sabse zyada bikne wale jeans konse hain?",
        "Mumbai store ki sales last 6 months ka trend",
        "VIP customers ka acquisition channel breakdown",
        
        # Follow-up examples
        "Aur Delhi ka batao",
        "Iska monthly breakdown chart mein",
        "Top 5 details mein dikhao",
    ]


def format_currency(value) -> str:
    """Format Indian currency."""
    try:
        value = float(value)
        if value >= 10000000:
            return f"₹{value/10000000:.2f} Cr"
        elif value >= 100000:
            return f"₹{value/100000:.2f} L"
        elif value >= 1000:
            return f"₹{value:,.0f}"
        else:
            return f"₹{value:.2f}"
    except (ValueError, TypeError):
        return str(value)
