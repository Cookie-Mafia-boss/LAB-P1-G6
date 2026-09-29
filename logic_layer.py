import re
from datetime import datetime, date

DATE_FORMAT = "%d/%m/%Y"
MAX_YEARS = 30

# Checks if the items are within the 30 year limit
def shift_years(d:date, years:int) -> date:
    """Move a date by N years"""
    return d.replace(year=d.year + years)

def validate_expiry_date(date_str: str, max_years: int = MAX_YEARS):
    """
    Returns (parsed_date, None) if valid, otherwise (None, error_message).
    Rejects malformed dates and dates more than `max_years` in the past or future.
    """
    try:
        exp_date = datetime.strptime(date_str.strip(), DATE_FORMAT).date()
    except ValueError:
        return None, "Invalid format. Please use DD/MM/YYYY (e.g. 25/12/2027)."
    
    today = datetime.now().date()
    earliest = shift_years(today, -max_years)
    latest = shift_years(today, max_years)
    
    if exp_date < earliest:
        return None, f"Expiry date is more than {max_years} years in the past."
    if exp_date > latest:
        return None, f"Expiry date is more than {max_years} years in the future."
    
    return exp_date, None

def validate_food_name(name: str):
    "Rejects empty names and integer inputs"
    cleaned = name.strip

    if not cleaned:
        return None, "Food name cannot be empty."

    if re.fullmatch(r"[+-]?\d+(\.\d+)?", cleaned):
        return None, "Food name cannot be a number. Please enter a valid food name (e.g. Milk)."

    return cleaned, None

# Checks Items with EXPIRING Status and makes/returns {Expiring soon}.
def check_expiries(inventory, alert_days=30):
    """Calculates days remaining using datetime module and reports alerts."""
    if not inventory:
        return []

    
    expiring_soon_items = []

    for item in inventory:
        if 0 < item["Days_Remaining"] <= alert_days:
            expiring_soon_items.append(item)


    # Sort items according to Days Remaining
    return sorted(expiring_soon_items, key=lambda x: x['Days_Remaining'])


def inventory_count(inventory):
    return len(inventory)