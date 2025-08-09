from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency_format(value):
    """
    Format a number with proper comma separators using standard formatting
    Example: 1000 -> "1,000", 100000 -> "100,000"
    """
    try:
        # Convert to int to remove decimal places
        amount = int(float(value))
        
        # Use Python's built-in formatting with commas
        return f"{amount:,}"
        
    except (ValueError, TypeError):
        return str(value)

@register.filter  
def inr_format(value):
    """
    Format a number as Indian Rupees with ₹ symbol
    Example: 1000 -> "₹1,000"
    """
    formatted_amount = currency_format(value)
    return f"₹{formatted_amount}"

@register.filter
def add_hex_prefix(value):
    """
    Ensure a transaction hash has the 0x prefix
    Example: "abc123" -> "0xabc123", "0xabc123" -> "0xabc123"
    """
    if not value:
        return value
    
    value_str = str(value).strip()
    if value_str.startswith('0x'):
        return value_str
    else:
        return f"0x{value_str}"

@register.filter
def div(value, arg):
    """Divide filter for template calculations"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply filter for template calculations"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 