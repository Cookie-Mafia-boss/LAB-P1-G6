import csv
from datetime import datetime, date

def expiry_alert(category: str = None):
    with open("../Dataset/food_inventory_dataset.csv", encoding="utf-8-sig") as f:
        table = list(csv.DictReader(f))

    result = []
    category_matched = False

    for row in table:
        # if category is not None and category.lower() != row["Category"].lower():
        #     continue

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