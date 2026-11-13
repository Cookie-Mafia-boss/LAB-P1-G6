import re
from datetime import datetime, date

#Encapsulates business rules, 
#parsing logic, and validations into InventoryValidator and InventoryLogic classes
class InventoryValidator:
    """Encapsulates validation rules for names, quantities, and dates."""
    
    DATE_FORMAT = "%d/%m/%Y"
    MAX_YEARS = 30

    @staticmethod
    def shift_years(d: date, years: int) -> date:
        """Move a date by N years."""
        return d.replace(year=d.year + years)

    @classmethod
    def validate_expiry_date(cls, date_str: str):
        """Validates expiry date limits and formats."""
        try:
            exp_date = datetime.strptime(date_str.strip(), cls.DATE_FORMAT).date()
        except ValueError:
            return None, "Invalid format. Please use DD/MM/YYYY (e.g. 25/12/2027)."
        
        today = datetime.now().date()
        earliest = cls.shift_years(today, -cls.MAX_YEARS)
        latest = cls.shift_years(today, cls.MAX_YEARS)
        
        if exp_date < earliest:
            return None, f"Expiry date is more than {cls.MAX_YEARS} years in the past."
        if exp_date > latest:
            return None, f"Expiry date is more than {cls.MAX_YEARS} years in the future."
        
        return exp_date, None

    @staticmethod
    def validate_food_name(name: str):
        """Rejects empty names and numeric-only strings."""
        cleaned = name.strip()
        if not cleaned:
            return None, "Food name cannot be empty."
        if re.fullmatch(r"[+-]?\d+(\.\d+)?", cleaned):
            return None, "Food name cannot be a number. Please enter a valid food name."
        return cleaned, None

    @staticmethod
    def validate_qty(qty):
        """Validates positive integer quantity."""
        error_msg = "Qty should be a positive integer"
        if not str(qty).isdigit():
            return None, error_msg
        qty_int = int(qty)
        if qty_int <= 0:
            return None, error_msg
        return qty_int, None


class InventoryLogic:
    """Encapsulates general core processing rules for the inventory."""

    @staticmethod
    def check_expiries(inventory, alert_days=30):
        """Filters and sorts expiring inventory items."""
        if not inventory:
            return []

        expiring_soon_items = []
        for item in inventory:
            if 0 < item["Days_Remaining"] <= alert_days:
                expiring_soon_items.append(item)

        return sorted(expiring_soon_items, key=lambda x: x['Days_Remaining'])

    @staticmethod
    def inventory_count(inventory):
        """Returns total item count."""
        return len(inventory)