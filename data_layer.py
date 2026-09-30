import csv
import os
from datetime import datetime
from rich import print

FILENAME = "./food_inventory_dataset.csv"
DATE_FORMAT = "%d/%m/%Y"
FIELDNAMES = [
    "Serial_Number",
    "Food_Name",
    "Expiry_Date",
    "Date_Purchased",
    "Inventory_Quantity",
    "Days_Remaining",
    "Status",
]


# Initialises inventory object on start from csv file
def initialise_inventory():
    """Loads inventory items from the CSV file if it exists."""
    inventory = []

    if not os.path.exists(FILENAME):
        print(f"[yellow]Warning:[/yellow] File '{FILENAME}' not found. Starting with an empty inventory.")
        return inventory

    try:
        with open(FILENAME, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            today = datetime.now().date()
            for row in reader:
                # Normalizes keys by stripping whitespace
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k}

                # Checks for key variations (e.g. Food_Name vs Food Name)
                serial_number = clean_row.get("Serial_Number") or clean_row.get("Serial Number")
                food_name = clean_row.get("Food_Name") or clean_row.get("Food Name")
                expiry_date = clean_row.get("Expiry_Date") or clean_row.get("Expiry Date")
                date_purchased = clean_row.get("Date_Purchased") or clean_row.get("Date Purchased")
                quantity_str = clean_row.get("Inventory_Quantity") or clean_row.get("Inventory Quantity")

                if not (food_name and expiry_date and date_purchased and quantity_str):
                    continue

                # Calculate days remaining
                exp_date = datetime.strptime(expiry_date, DATE_FORMAT).date()
                days_remaining = (exp_date - today).days

                # Determine status
                if days_remaining <= 0:
                    status = "EXPIRED"
                elif days_remaining <= 30:
                    status = "EXPIRING"
                else:
                    status = "FRESH"

                try:
                    inventory.append({
                        "Serial_Number": serial_number,
                        "Food_Name": food_name,
                        "Expiry_Date": expiry_date,
                        "Date_Purchased": date_purchased,
                        "Inventory_Quantity": int(quantity_str),
                        "Days_Remaining": int(days_remaining),
                        "Status": status
                    })
                except ValueError:  
                    continue  # Skip row if quantity is not a valid integer

        print(f"[green]Success:[/green] Successfully loaded {len(inventory)} items from '{FILENAME}'.")
    except Exception as e:
        print(f"[red]Error:[/red] Error reading file: {e}")

    return inventory




def save_inventory(items):
    if len(items) != 0:
        with open(FILENAME, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(items)

