import csv
from datetime import datetime
import os

def load_inventory(FILENAME):
    inventory = []
    if not os.path.exists(FILENAME):
        print(f"⚠️ Warning: File '{FILENAME}' not found. Starting with an empty inventory.")
        return inventory
    try:
        with open(FILENAME, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            inventory = list(reader)
        return inventory

    except Exception as e:
        print(f"❌ Error reading file: {e}")