import csv
import os
from datetime import datetime
from rich import print

#Encapsulates CSV input/output operations into an InventoryRepository class.
class InventoryRepository:
    """Handles loading and saving inventory data to and from CSV storage."""

    def __init__(self, filename="./food_inventory_dataset.csv"):
        self.filename = filename
        self.fieldnames = [
            "Serial_Number",
            "Food_Name",
            "Expiry_Date",
            "Date_Purchased",
            "Inventory_Quantity",
            "Days_Remaining",
            "Status",
        ]

    def load_inventory(self):
        """Loads inventory items from the CSV file if it exists."""
        inventory = []

        if not os.path.exists(self.filename):
            print(f"[yellow]Warning:[/yellow] File '{self.filename}' not found. Starting with an empty inventory.")
            return inventory

        try:
            with open(self.filename, mode="r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                today = datetime.now().date()
                for row in reader:
                    clean_row = {k.strip(): v.strip() for k, v in row.items() if k}

                    serial_number = clean_row.get("Serial_Number") or clean_row.get("Serial Number")
                    food_name = clean_row.get("Food_Name") or clean_row.get("Food Name")
                    expiry_date = clean_row.get("Expiry_Date") or clean_row.get("Expiry Date")
                    date_purchased = clean_row.get("Date_Purchased") or clean_row.get("Date Purchased")
                    quantity_str = clean_row.get("Inventory_Quantity") or clean_row.get("Inventory Quantity")

                    if not (food_name and expiry_date and date_purchased and quantity_str):
                        continue

                    exp_date = datetime.strptime(expiry_date, "%d/%m/%Y").date()
                    days_remaining = (exp_date - today).days

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
                        continue  

            print(f"[green]Success:[/green] Successfully loaded {len(inventory)} items from '{self.filename}'.")
        except Exception as e:
            print(f"[red]Error:[/red] Error reading file: {e}")

        return inventory

    def save_inventory(self, items):
        """Saves current inventory items to CSV storage."""
        if len(items) != 0:
            with open(self.filename, mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(items)