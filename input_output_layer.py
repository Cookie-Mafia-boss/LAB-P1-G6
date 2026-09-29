import ctypes
import os
from datetime import datetime
from rich import print
from rich.table import Table

from logic_layer import inventory_count

DATE_FORMAT = "%d/%m/%Y"


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
        raw_status = item["Status"]
        
        # Check status and set formatted markup string without modifying inventory dict
        if "EXPIRED" in raw_status:
            status_formatted = "[bold red]EXPIRED[/bold red]"
        elif "EXPIRING" in raw_status:
            status_formatted = "[bold yellow]EXPIRING[/bold yellow]"
        elif "FRESH" in raw_status:
            status_formatted = "[bold green]FRESH[/bold green]"
        else:
            status_formatted = raw_status

        table.add_row(
            item["Food_Name"],
            str(item["Inventory_Quantity"]),
            item["Expiry_Date"],
            str(item["Days_Remaining"]),
            status_formatted
        )
    return table


def raise_alert(expiring_inventory):
    if len(expiring_inventory) > 0:
        expire_alert(expiring_inventory)


def do_nothing():
    print("User clicked No.")


def expire_alert(expiring_inventory):
    alert_title = 'Items are about to expire!'
    alert_text = f"{inventory_count(expiring_inventory)} items are about to expire! Would you like to view them?"
    
    # Windows native popup fallback for cross-platform safety
    if os.name == 'nt':
        result = ctypes.windll.user32.MessageBoxW(0, alert_text, alert_title, 4)
        if result == 6:  # Yes
            print(display_items(expiring_inventory, "Expiring Items"))
        elif result == 7:  # No
            do_nothing()
    else:
        # Standard CLI prompt for non-Windows platforms (macOS/Linux)
        choice = input(f"\n⚠️ {alert_text} (y/n): ").strip().lower()
        if choice == 'y':
            print(display_items(expiring_inventory, "Expiring Items"))
        else:
            do_nothing()


def add_food_item(inventory):
    """Stub function to allow adding items manually."""
    print("\n--- Add New Food Item ---")
    name = input("Enter food name: ").strip()
    qty = input("Enter quantity: ").strip()
    exp_date = input(f"Enter expiry date ({DATE_FORMAT}): ").strip()
    purch_date = datetime.now().strftime(DATE_FORMAT)

    try:
        exp_dt = datetime.strptime(exp_date, DATE_FORMAT).date()
        days_rem = (exp_dt - datetime.now().date()).days
        
        if days_rem < 0:
            status = "EXPIRED"
        elif days_rem <= 30:
            status = "EXPIRING"
        else:
            status = "FRESH"

        inventory.append({
            "Food_Name": name,
            "Expiry_Date": exp_date,
            "Date_Purchased": purch_date,
            "Inventory_Quantity": int(qty),
            "Days_Remaining": days_rem,
            "Status": status
        })
        print(f"✅ Added '{name}' successfully!")
    except Exception as e:
        print(f"❌ Failed to add item: {e}")