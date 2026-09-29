import csv
import os
from datetime import datetime
from rich import print

FILENAME = "./food_inventory_dataset.csv"
DATE_FORMAT = "%d/%m/%Y"
FIELDNAMES = [
    "Food_Name",
    "Expiry_Date",
    "Date_Purchased",
    "Inventory_Quantity",
    "Days_Remaining",
    "Status"
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

def save_item_to_csv(item):
    """Appends a single item to the CSV file."""
    fieldnames = FIELDNAMES
    needs_newline = False
    file_has_content = os.path.exists(FILENAME) and os.path.getsize(FILENAME) > 0

    if file_has_content:
        # Reuse whatever header the file already has, so columns stay lined up
        with open(FILENAME, mode="r", encoding="utf-8-sig", newline="") as f:
            header = next(csv.reader(f), None)
            if header:
                fieldnames = [h.strip() for h in header]

        # If the last line has no newline, the new row would get glued onto it
        with open(FILENAME, mode="rb") as f:
            f.seek(-1, os.SEEK_END)
            needs_newline = f.read(1) not in (b"\n", b"\r")

    # Handles headers like "Food Name" as well as "Food_Name"
    row = {name: item.get(name.replace(" ", "_"), "") for name in fieldnames}

    with open(FILENAME, mode="a", encoding="utf-8", newline="") as f:
        if needs_newline:
            f.write("\r\n")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_has_content:
            writer.writeheader()
        writer.writerow(row)