import csv
from datetime import datetime, date
import os
import sys
import os

# Add the project root (parent of AI_Layer) to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Data_Layer import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up one level to project root, then into Dataset/
FILENAME = os.path.join(BASE_DIR, "..", "Dataset", "food_inventory_dataset.csv")
FILENAME = os.path.normpath(FILENAME) 

def expiry_alert(category: str = None):
    """Check the food inventory for items expiring within 5 days.

    Args:
        category: Optional. Filter by exact category name if the user asks
            about a specific type of food. Valid values: 'Dairy', 'Meat & Seafood',
            'Produce', 'Bakery', 'Pantry', 'Frozen', 'Beverages'. Leave as None
            to check the entire inventory across all categories.
    """
    print(">>> TOOL CALLED with category:", category)
    table = load_inventory(FILENAME)

    result = []
    category_matched = False

    for row in table:
        if category is not None and category.lower() != row["Category"].lower():
            continue

        category_matched = True

        days_to_exp = (datetime.strptime(row["Expiry_Date"], "%d/%m/%Y").date() - date.today()).days
        if days_to_exp > 5:
            continue

        result.append(f"{row['Food_Name']} | {days_to_exp} days left | qty {row['Inventory_Quantity']}")

    if not category_matched:
        return "No matching items found."
    elif not result:
        return "Nice, no items approaching their expiry dates."
    else:
        return "\n".join(result)





TOOLS = {"expiry_alert": expiry_alert}