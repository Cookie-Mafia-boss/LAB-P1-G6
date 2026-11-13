"""Public entry points used by main.py and the other application layers.

Keeps the same function names the rest of the project already uses:
    initialise_inventory()      -> Inventory
    save_inventory(inventory)   -> persists the Inventory to SQLite
"""

import atexit
from pathlib import Path

from rich import print

from classes.csv_migrator import CSVMigrator
from classes.data_exceptions import DataLayerError
from classes.data_manager import DataManager
from classes.sqlite_repository import SQLiteRepository

PROJECT_FOLDER = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_FOLDER / "food_inventory.db"
CSV_PATH = PROJECT_FOLDER / "food_inventory_dataset.csv"

_data_manager = None


def get_data_manager():
    """Return the shared DataManager instance, creating it when necessary."""
    global _data_manager
    if _data_manager is None:
        repository = SQLiteRepository(DATABASE_PATH)
        _data_manager = DataManager(repository)
    return _data_manager


def initialise_inventory():
    """Load the database into an Inventory object.

    On the very first run, if the original CSV exists, it is imported once.
    A flag is stored in the database so that emptying the inventory later
    does not cause the CSV to be re-imported.
    """
    manager = get_data_manager()

    if not manager.is_csv_imported():
        if CSV_PATH.exists() and not manager.get_all_items():
            try:
                result = CSVMigrator(manager).migrate(CSV_PATH)
                print(
                    "[green]CSV import complete:[/green] "
                    f"{result['imported']} imported, {result['skipped']} skipped."
                )
                for message in result["errors"][:5]:
                    print(f"[yellow]  {message}[/yellow]")
            except DataLayerError as error:
                print(f"[red]Error:[/red] CSV import failed: {error}")
                return manager.load_inventory()  # try again next run
        elif not CSV_PATH.exists():
            print(
                f"[yellow]Warning:[/yellow] '{CSV_PATH.name}' not found. "
                "Starting with an empty inventory."
            )
        manager.mark_csv_imported()

    inventory = manager.load_inventory()
    # Items recalculate days_remaining/status on load; keep DB columns fresh.
    manager.refresh_stored_status(inventory)
    return inventory


def save_inventory(inventory):
    """Persist the in-memory Inventory to the database."""
    try:
        get_data_manager().save_inventory(inventory)
    except DataLayerError as error:
        print(f"[red]Error:[/red] Could not save inventory: {error}")


def close_database():
    """Close the shared database connection (also runs automatically on exit)."""
    global _data_manager
    if _data_manager is not None:
        _data_manager.close()
        _data_manager = None


atexit.register(close_database)
