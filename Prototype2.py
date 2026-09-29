import ctypes
import csv
from datetime import datetime
import os
#colour coding
from rich import print
from rich.table import Table

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


#Initialises inventory object on start from csv file

def initialise_inventory():
    """Loads inventory items from the CSV file if it exists."""
    inventory = []

    if not os.path.exists(FILENAME):
        print(f"⚠️ Warning: File '{FILENAME}' not found. Starting with an empty inventory.")
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

                #calculate days remaining
                exp_date = datetime.strptime(
                    expiry_date, DATE_FORMAT
                ).date()
                days_remaining = (exp_date - today).days

                #determine status
                if(days_remaining < 0):
                    status = "EXPIRED"
                elif(days_remaining <= 30):
                    status = "EXPIRING"
                elif(days_remaining > 30):
                    status = "FRESH"

                #append each item to the inventory list
                if food_name and expiry_date and date_purchased and quantity_str:
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

        print(f"✅ Successfully loaded {len(inventory)} items from '{FILENAME}'.")
    except Exception as e:
        print(f"❌ Error reading file: {e}")

    return inventory


# Generates table to display all items in object. Requires {Inventory}, "Title"

def display_items(inventory, title):

    # Create table structure
    table = Table(title=title, show_header=True, header_style="bold purple")

    # Add columns with alignments and colors
    table.add_column("Food Name", no_wrap=True)
    table.add_column("Qty", style="cyan", justify="center")
    table.add_column("Expiry Date", style="cyan", justify="center")
    table.add_column("Days Left", style="cyan", justify="center")
    table.add_column("Status", justify="right")

    # Add data rows
    for item in inventory:

        #check status and apply color coding
        if item["Status"] == "EXPIRED":
            item["Status"] = "[bold red]EXPIRED[/bold red]"
        elif item["Status"] == "EXPIRING":
            item["Status"] = "[bold yellow]EXPIRING[/bold yellow]"
        elif item["Status"] == "FRESH":
            item["Status"] = "[bold green]FRESH[/bold green]"

        table.add_row(
            item["Food_Name"],
            str(item["Inventory_Quantity"]),
            item["Expiry_Date"],
            str(item["Days_Remaining"]),
            str(item["Status"])
        )
    return table


# Checks Items with EXPIRING Status and makes/returns {Expiring soon}. Requires {Inventory}

def check_expiries(inventory):
    """Calculates days remaining using datetime module and reports alerts."""
    if not inventory:
        print("\nInventory is empty.")
        return

    expiring_soon_items = []

    for item in inventory:
        if item["Status"] == "EXPIRING":
            expiring_soon_items.append(item)

    #sort items according to Days Remaining
    sorted_expiring_soon_items = sorted(expiring_soon_items, key=lambda x: x['Days_Remaining'])
    return sorted_expiring_soon_items

def raise_alert(expiring_inventory):
    if len(expiring_inventory) > 0:
        expire_alert(expiring_inventory)
    else:
        #do nothing
        pass

def inventory_count(inventory):
    item_count = 0
    for item in inventory:
        item_count+=1
    return item_count


def do_nothing():
    print("User clicked No.")

def expire_alert(expiring_inventory):
    alert_title = 'Items are about to expire!'
    alert_text = f"{inventory_count(expiring_inventory)} items are about to expire! Would you like to view them?"
    result = ctypes.windll.user32.MessageBoxW(0, alert_text, alert_title, 4)

    if result == 6:  # Yes
        print(display_items(expiring_inventory, "Expiring Items"))
    elif result == 7:  # No
        do_nothing()

inventory = initialise_inventory()
raise_alert(check_expiries(inventory))
print(display_items(inventory, "Inventory"))