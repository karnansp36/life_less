from datetime import datetime, date
from typing import Any, Dict, List
import json

def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default

def calculate_time_window(days: int = 30) -> tuple:
    """Calculate start and end dates for a time window"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis if too long"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'