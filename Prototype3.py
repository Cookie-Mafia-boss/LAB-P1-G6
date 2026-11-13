import ctypes
import csv
from datetime import datetime
import json
import os

# Colour coding
from rich import print
from rich.table import Table

# AI API (pip install google-genai)
from google import genai

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

                if not (food_name and expiry_date and date_purchased and quantity_str):
                    continue

                # Calculate days remaining
                exp_date = datetime.strptime(expiry_date, DATE_FORMAT).date()
                days_remaining = (exp_date - today).days

                # Determine status
                if days_remaining < 0:
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


# Checks Items with EXPIRING Status and makes/returns {Expiring soon}.
def check_expiries(inventory, alert_days=30):
    """Calculates days remaining using datetime module and reports alerts."""
    if not inventory:
        return []

    expiring_soon_items = []

    for item in inventory:
        if 0 <= item["Days_Remaining"] <= alert_days:
            expiring_soon_items.append(item)

    # Sort items according to Days Remaining
    return sorted(expiring_soon_items, key=lambda x: x['Days_Remaining'])


def raise_alert(expiring_inventory):
    if len(expiring_inventory) > 0:
        expire_alert(expiring_inventory)


def inventory_count(inventory):
    return len(inventory)


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


# ==========================================
# AI LAYER (Interactions API)
# ==========================================
def get_ai_suggestions(inventory, expiring_items):
    """Sends food inventory payload to Gemini using the Interactions API."""
    print("\n🤖 [bold cyan]Analyzing Inventory with AI...[/bold cyan]")
    
    if not inventory:
        print("⚠️ Inventory is empty. Add items to analyze with the AI model.")
        return

    # STEP 1: Extract and prepare data for your AI payload
    expired_list = [item['Food_Name'] for item in inventory if item['Status'] == 'EXPIRED']
    expiring_list = [item['Food_Name'] for item in expiring_items]
    
    payload_data = {
        "total_items": len(inventory),
        "expired_items": expired_list,
        "expiring_soon": expiring_list,
        "raw_inventory": inventory
    }

    # STEP 2: Format the payload dictionary into a string prompt
    prompt = f"""
    You are an AI kitchen assistant and food waste prevention specialist.
    Based on this inventory data:
        1. Suggest 2-3 actionable, delicious recipes to prioritize using up items with the fewest days remaining.
        2. Provide Waste Trends (How much food has been wasted due to expiry or will potentially be wasted/How much food you have saved before its expiry.)
        3. Call out any items requiring immediate action.
        4. Suggest Resupplying Recommendations (Prevent overstocking of food)


    Inventory Data:
    {json.dumps(payload_data, indent=2)}
    """

    # STEP 3: Call the Interactions API
    try:
        client = genai.Client()

        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )

        print("\n--- 💡 AI Recipe & Waste Prevention Suggestions ---")
        print(interaction.output_text)

    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")


# ==========================================
# MAIN MENU LOOP
# ==========================================
def main_menu():
    """Runs the interactive CLI menu loop."""
    inventory = initialise_inventory()
    
    # Check for initial startup alerts
    expiring_items = check_expiries(inventory)
    raise_alert(expiring_items)

    while True:
        system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("\n=== FOOD WASTE MANAGEMENT SYSTEM ===")
        print(f"Current time : {system_time}")
        print("1. View Inventory")
        print("2. Add New Food Item")
        print("3. Check Expiry Alerts")
        print("4. Get AI suggestions for expired food and waste trends")
        print("5. Exit")

        choice = input("Select an option (1-5): ").strip()

        if choice == "1":
            print(display_items(inventory, "Current Food Inventory"))
        elif choice == "2":
            add_food_item(inventory)
        elif choice == "3":
            try:
                days = input("Enter warning threshold in days [Default: 30]: ").strip()
                days = int(days) if days else 30
            except ValueError:
                days = 30
            expiring = check_expiries(inventory, alert_days=days)
            if expiring:
                print(display_items(expiring, f"Items Expiring Within {days} Days"))
            else:
                print(f"✅ No items expiring within {days} days.")
        elif choice == "4":
            expiring = check_expiries(inventory)
            get_ai_suggestions(inventory, expiring)
        elif choice == "5":
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid selection. Please enter a number from 1 to 5.")


if __name__ == "__main__":
    main_menu()