from datetime import datetime
from rich import print
from rich.console import Console

console = Console()

from data_layer import initialise_inventory, save_inventory
from logic_layer import check_expiries
from ai_layer import get_ai_suggestions
from input_output_layer import display_items, raise_alert, add_food_item, display_ai_suggestions, display_ai_summary_stats, delete_food_item, update_food_item


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
        print("3. Delete Food Item")
        print("4. Update Food Item")
        print("5. Check Expiry Alerts")
        print("6. Get AI suggestions for expired food and waste trends")
        print("7. Exit")

        choice = input("Select an option (1-7): ").strip()

        if choice == "1":
            print(display_items(inventory, "Current Food Inventory"))
        elif choice == "2":
            add_food_item(inventory)
        elif choice == "3":
            delete_food_item(inventory)
        elif choice == "4":
            update_food_item(inventory)
        elif choice == "5":
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
        elif choice == "6":
            expiring = check_expiries(inventory)
            console.print("[cyan]Analyzing inventory with AI...[/cyan]")
            sections = get_ai_suggestions(inventory, expiring)
            display_ai_suggestions(sections)
            display_ai_summary_stats(inventory, expiring)
        elif choice == "7":
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid selection. Please enter a number from 1 to 7.")

        save_inventory(inventory)


if __name__ == "__main__":
    main_menu()