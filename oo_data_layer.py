from datetime import datetime
from typing import Dict, List, Optional, Union
from pymongo import MongoClient, UpdateOne


MONGO_URI = "mongodb+srv://thetotalstrain_db_user:00u0kBhWrW2iItbO@foodwastemanagement.0mkj7tn.mongodb.net/"
DB_NAME = "food_waste_db"
COLLECTION_NAME = "inventory"


class InventoryRepository:
    """Data Access Object (DAO) for managing MongoDB persistence using standard CRUD operations."""

    def __init__(self, uri: str = MONGO_URI, db_name: str = DB_NAME):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[COLLECTION_NAME]
        self._init_db()

    def _init_db(self) -> None:
        self.collection.create_index("serial_number", unique=True)

    #convert into Model
    def add_item(self, item: Dict[str, Union[str, int]]) -> None:
        mongo_doc = {
            "serial_number": item["Serial_Number"],
            "food_name": item["Food_Name"],
            "expiry_date": item["Expiry_Date"],
            "date_purchased": item["Date_Purchased"],
            "quantity": int(item["Inventory_Quantity"]),
            "days_remaining": int(item["Days_Remaining"]),
            "status": str(item["Status"]),
        }
        self.collection.insert_one(mongo_doc)

    def update_item(self, item: Dict[str, Union[str, int]]) -> None:
        self.collection.update_one(
            {"serial_number": item["Serial_Number"]},
            {
                "$set": {
                    "food_name": item["Food_Name"],
                    "expiry_date": item["Expiry_Date"],
                    "date_purchased": item["Date_Purchased"],
                    "quantity": int(item["Inventory_Quantity"]),
                    "days_remaining": int(item["Days_Remaining"]),
                    "status": str(item["Status"]),
                }
            },
        )

    def delete_item(self, serial_number: str) -> None:
        self.collection.delete_one({"serial_number": serial_number})

    def load_inventory(self) -> List[Dict[str, Union[str, int]]]:
        today = datetime.now().date()
        inventory = []

        # Find all items sorting by serial_number ascending (1)
        cursor = self.collection.find({}).sort("serial_number", 1)

        for doc in cursor:
            try:
                exp_dt = datetime.strptime(
                    doc["expiry_date"], "%d/%m/%Y"
                ).date()
                days_rem = (exp_dt - today).days
            except ValueError:
                days_rem = doc["days_remaining"]

            if days_rem <= 0:
                status = "EXPIRED"
            elif days_rem <= 30:
                status = "EXPIRING"
            else:
                status = "FRESH"

            inventory.append(
                {
                    "Serial_Number": doc["serial_number"],
                    "Food_Name": doc["food_name"],
                    "Expiry_Date": doc["expiry_date"],
                    "Date_Purchased": doc["date_purchased"],
                    "Inventory_Quantity": doc["quantity"],
                    "Days_Remaining": days_rem,
                    "Status": status,
                }
            )

        return inventory

    def save_inventory(
        self, inventory: List[Dict[str, Union[str, int]]]
    ) -> None:
        """Bulk synchronizes the full state using an atomic UPSERT bulk write operation."""
        if not inventory:
            return

        operations = []
        for item in inventory:
            operations.append(
                UpdateOne(
                    {"serial_number": item["Serial_Number"]},
                    {
                        "$set": {
                            "food_name": item["Food_Name"],
                            "expiry_date": item["Expiry_Date"],
                            "date_purchased": item["Date_Purchased"],
                            "quantity": int(item["Inventory_Quantity"]),
                            "days_remaining": int(item["Days_Remaining"]),
                            "status": str(item["Status"]),
                        }
                    },
                    upsert=True,  # Inserts document if serial_number isn't found
                )
            )

        self.collection.bulk_write(operations)
