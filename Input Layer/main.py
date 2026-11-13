import csv
from datetime import datetime
import os
#colour coding
from rich import print


FILENAME = "../Dataset/food_inventory_dataset.csv"
DATE_FORMAT = "%d/%m/%Y"
FIELDNAMES = [
    "Food_Name",
    "Expiry_Date",
    "Date_Purchased",
    "Inventory_Quantity",
]

#open csv file and load csv data onto the datatable
def load_from_csv():
    """Loads inventory items from the CSV file if it exists."""
    inventory = []

    if not os.path.exists(FILENAME):
        print(f"⚠️ Warning: File '{FILENAME}' not found. Starting with an empty inventory.")
        return inventory

    try:
        with open(FILENAME, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Normalizes keys by stripping whitespace
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k}

                # Checks for key variations (e.g. Food_Name vs Food Name)
                food_name = clean_row.get("Food_Name") or clean_row.get("Food Name")
                expiry_date = clean_row.get("Expiry_Date") or clean_row.get("Expiry Date")
                date_purchased = clean_row.get("Date_Purchased") or clean_row.get("Date Purchased")
                quantity_str = clean_row.get("Inventory_Quantity") or clean_row.get("Inventory Quantity")

                if food_name and expiry_date and date_purchased and quantity_str:
                    try:
                        inventory.append({
                            "Food_Name": food_name,
                            "Expiry_Date": expiry_date,
                            "Date_Purchased": date_purchased,
                            "Inventory_Quantity": int(quantity_str),
                        })
                    except ValueError:
                        continue  # Skip row if quantity is not a valid integer

        print(f"✅ Successfully loaded {len(inventory)} items from '{FILENAME}'.")
    except Exception as e:
        print(f"❌ Error reading file: {e}")

    return inventory


def save_to_csv(inventory):
    """Writes the current inventory back to the CSV file."""
    #error handling
    try:
        with open(FILENAME, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(inventory)
        print(f"💾 Changes saved to '{FILENAME}'.")
    except Exception as e:
        print(f"❌ Error saving to file: {e}")


# ==========================================
# DATA VALIDATION HELPER FUNCTIONS
# ==========================================


def get_valid_food_name():
    """Ensures food name is not empty."""
    while True:
        name = input("Enter Food Name: ").strip().title()
        if name:
            return name
        print("❌ Food name cannot be empty. Please try again.")



def get_valid_expiry_date():
    """Validates date format and ensures expiry date is in the future."""
    today = datetime.now().date()

    while True:
        date_str = input("Enter Expiry Date (DD/MM/YYYY): ").strip()
        try:
            parsed_date = datetime.strptime(date_str, DATE_FORMAT).date()

            if parsed_date <= today:
                print(
                    f"❌ Expiry date must be in the future (after {today.strftime(DATE_FORMAT)})."
                )
                continue

            return date_str

        except ValueError:
            print(
                "❌ Invalid format! Please use DD/MM/YYYY (e.g., 25/12/2027)."
            )


def get_valid_purchase_date():
    """Validates purchase date format and ensures it is not in the future."""
    today = datetime.now().date()

    while True:
        date_str = input(
            "Enter Purchase Date (DD/MM/YYYY) [Press Enter for Today]: "
        ).strip()

        if not date_str:
            return today.strftime(DATE_FORMAT)

        try:
            parsed_date = datetime.strptime(date_str, DATE_FORMAT).date()

            if parsed_date > today:
                print("❌ Purchase date cannot be in the future.")
                continue

            return date_str

        except ValueError:
            print(
                "❌ Invalid format! Please use DD/MM/YYYY (e.g., 05/08/2026)."
            )


def get_valid_quantity():
    """Validates that inventory quantity is a positive whole number."""
    while True:
        qty_str = input("Enter Inventory Quantity: ").strip()

        try:
            qty = int(qty_str)

            if qty <= 0:
                print("❌ Quantity must be greater than 0.")
                continue

            return qty

        except ValueError:
            print("❌ Invalid input! Please enter a whole number (e.g., 10).")


# ==========================================
# CLI CORE FEATURES
# ==========================================
def add_food_item(inventory):
    """CLI function to collect validated data for a new food item and update file."""
    print("\n--- ADD NEW FOOD ITEM ---")

    name = get_valid_food_name()
    exp_date = get_valid_expiry_date()
    pur_date = get_valid_purchase_date()
    quantity = get_valid_quantity()

    pur_dt = datetime.strptime(pur_date, DATE_FORMAT)
    exp_dt = datetime.strptime(exp_date, DATE_FORMAT)

    if pur_dt >= exp_dt:
        print(
            "\n❌ Error: Expiry date must be after the purchase date. Item not added."
        )
        return

    new_item = {
        "Food_Name": name,
        "Expiry_Date": exp_date,
        "Date_Purchased": pur_date,
        "Inventory_Quantity": quantity,
    }

    inventory.append(new_item)
    save_to_csv(inventory)
    print(f" [+] '{name}' successfully added to inventory!")


def view_inventory(inventory):
    """Displays current inventory in a formatted table layout."""
    if not inventory:
        print("\nInventory is currently empty.")
        return

    print("\n" + "=" * 80)
    print(
        f"{'Food Name':<20} | {'Qty':<5} | {'Purchased':<12} | {'Expiry Date':<12}"
    )
    print("=" * 80)
    for item in inventory:
        print(
            f"{item['Food_Name']:<20} | {item['Inventory_Quantity']:<5} | {item['Date_Purchased']:<12} | {item['Expiry_Date']:<12}"
        )
    print("=" * 80)


def check_expiries(inventory, alert_days=30):
    """Calculates days remaining using datetime module and reports alerts."""
    if not inventory:
        print("\nInventory is empty.")
        return

    today = datetime.now().date()
    expired_items = []
    expiring_soon_items = []

    print("\n" + "=" * 80)
    print(
        f"{'Food Name':<20} | {'Qty':<5} | {'Expiry Date':<12} | {'Days Left':<10} | {'Status':<10}"
    )
    print("=" * 80)

    for item in inventory:
        try:
            exp_date = datetime.strptime(
                item["Expiry_Date"], DATE_FORMAT
            ).date()
        except ValueError:
            continue

        days_remaining = (exp_date - today).days

        if days_remaining < 0:
            status = "EXPIRED"
            expired_items.append(item["Food_Name"])
        elif days_remaining <= alert_days:
            #color coded to red
            status = "[red]EXPIRING[/red]"
            expiring_soon_items.append(item["Food_Name"])
        else:
            #color coded to green
            status = "[green]FRESH[/green]"

        print(
            f"{item['Food_Name']:<20} | {item['Inventory_Quantity']:<5} | {item['Expiry_Date']:<12} | {days_remaining:<10} | {status:<10}"
        )

    print("=" * 80)
    print(
        f"\n[!] Expired Items ({len(expired_items)}): {', '.join(expired_items) if expired_items else 'None'}"
    )
    print(
        f"[!] Expiring within {alert_days} days ({len(expiring_soon_items)}): {', '.join(expiring_soon_items) if expiring_soon_items else 'None'}\n"
    )


# ==========================================
# MAIN MENU LOOP
# ==========================================
def main_menu():
    """Runs the interactive CLI menu loop."""
    inventory = load_from_csv()

    while True:
        #displays current time
        system_time = datetime.now()

        print("\n=== FOOD WASTE MANAGEMENT SYSTEM  ===")
        print(f"Current time : {system_time}")
        print("1. View Inventory")
        print("2. Add New Food Item")
        print("3. Check Expiry Alerts")
        print("4. Exit")


        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            view_inventory(inventory)
        elif choice == "2":
            add_food_item(inventory)
        elif choice == "3":
            try:
                days = input("Enter warning threshold in days [Default: 30]: ").strip()
                days = int(days) if days else 30
            except ValueError:
                days = 30
            check_expiries(inventory, alert_days=days)
        elif choice == "4":
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid selection. Please enter a number from 1 to 4.")
        

if __name__ == "__main__":
    main_menu()