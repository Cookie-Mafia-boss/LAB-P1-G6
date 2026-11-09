from datetime import datetime
from rich import print
from rich.console import Console

from oo_data_layer import InventoryRepository
from oo_logic_layer import InventoryLogic
from oo_ai_layer import AIService
from oo_input_output_layer import ConsoleUI

#Encapsulates the application controller logic into a FoodWasteApp class
class FoodWasteApp:
    """Main application controller orchestrating layers and the CLI loop."""

    def __init__(self):
        self.console = Console()
        self.repository = InventoryRepository()
        self.ui = ConsoleUI()

    def run(self):
        """Runs the interactive CLI menu loop."""
        inventory = self.repository.load_inventory()
        
        # Check for initial startup alerts
        expiring_items = InventoryLogic.check_expiries(inventory)
        self.ui.raise_alert(expiring_items)

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
                table = self.ui.display_items(inventory, "Current Food Inventory")
                print(table)
            elif choice == "2":
                self.ui.add_food_item(inventory)
            elif choice == "3":
                self.ui.delete_food_item(inventory)
            elif choice == "4":
                self.ui.update_food_item(inventory)
            elif choice == "5":
                try:
                    days = input("Enter warning threshold in days [Default: 30]: ").strip()
                    days = int(days) if days else 30
                except ValueError:
                    days = 30
                expiring = InventoryLogic.check_expiries(inventory, alert_days=days)
                if expiring:
                    table = self.ui.display_items(expiring, f"Items Expiring Within {days} Days")
                    print(table)
                else:
                    print(f"✅ No items expiring within {days} days.")
            elif choice == "6":
                expiring = InventoryLogic.check_expiries(inventory)
                self.console.print("[cyan]Analyzing inventory with AI...[/cyan]")
                sections = AIService.get_ai_suggestions(inventory, expiring)
                self.ui.display_ai_suggestions(sections)
                self.ui.display_ai_summary_stats(inventory, expiring)
            elif choice == "7":
                print("Exiting application. Goodbye!")
                break
            else:
                print("Invalid selection. Please enter a number from 1 to 7.")

            self.repository.save_inventory(inventory)


if __name__ == "__main__":
    app = FoodWasteApp()
    app.run()