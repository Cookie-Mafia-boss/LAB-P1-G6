from datetime import datetime
from rich import print
from rich.console import Console

console = Console()

from data_layer import initialise_inventory, save_inventory
# from logic_layer import check_expiries
from ai_layer import AIService
from input_output_layer import (
    display_items, expire_alert, check_expires,
    add_food_item, delete_food_item, update_food_item, 
    display_ai_response, display_inventory_stats,
    )

def inventory_to_prompt_list(inventory):
    return [
        {
            "food_name": item.food_name,
            "inventory_quantity": item.inventory_quantity,
            "expiry_date": item.expiry_date,
            "days_remaining": item.days_remaining,
            "status": item.status,
        }
        for item in inventory.get_items()
    ]

"""
WARNING: USE THIS IF YOU DO NOT WANT TO EXCEED THE GEMINI INPUT TOKEN LIMIT

def inventory_to_prompt_list(inventory):
    items = inventory.get_items()
    interesting = [i for i in items if i.status in ("EXPIRED", "EXPIRING")] or items
    return [ { ... } for i in interesting[:50] ]
"""

#Encapsulates the application controller logic into a FoodWasteApp class.
# ==========================================
# MAIN MENU LOOP
# ==========================================
def main_menu():
    """Runs the interactive CLI menu loop."""
    inventory = initialise_inventory()
    ai_service = AIService()
    
    # Check for initial startup alerts
    # print(inventory.get_items())
    # expiring_items = display_items(inventory.get_expiring_items(), "Expiring Items")
    expire_alert(inventory.expiring_items())

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
            save_inventory(inventory)
        elif choice == "3":
            delete_food_item(inventory)
            save_inventory(inventory)
        elif choice == "4":
            update_food_item(inventory)
            save_inventory(inventory)
        elif choice == "5":
            check_expires(inventory)
        elif choice == "6":
            console.print("[cyan]Analyzing inventory with AI...[/cyan]")
            response = ai_service.process_inventory(inventory_to_prompt_list(inventory))
            display_ai_response(response)
            display_inventory_stats(inventory)
        elif choice == "7":
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid selection. Please enter a number from 1 to 7.")

        save_inventory(inventory)


if __name__ == "__main__":
    main_menu()