"""Application-facing manager that coordinates inventory and storage."""

from classes.inventory import Inventory


class DataManager:
    """Provides a simple interface between the program and its repository.

    The repository is injected into this class. DataManager does not need to
    know whether the data is stored in SQLite, a CSV file, or another system.

    add_item / update_item / delete_item accept an optional ``inventory``.
    When it is given, the in-memory Inventory is kept in step with the
    database in the same call, so other layers cannot forget one half.
    """

    def __init__(self, repository):
        self.repository = repository

    # ----- create / update / delete (database + optional in-memory sync) -----

    def add_item(self, item, inventory=None):
        """Save a new item to the database (and the inventory, if supplied)."""
        saved = self.repository.create(item)  # raises DuplicateRecordError
        if inventory is not None:
            inventory.add_item(item)
        return saved

    def update_item(self, item, inventory=None):
        """Save changes to an existing item.

        Call ``item.update(...)`` first so days_remaining and status are
        recalculated before they are written to the database.
        """
        saved = self.repository.update(item)  # raises RecordNotFoundError
        if inventory is not None:
            existing = inventory.search_item_by_serial(item.serial_number)
            if existing is None:
                inventory.add_item(item)
            elif existing is not item:
                inventory.remove_item(existing)
                inventory.add_item(item)
        return saved

    def delete_item(self, serial_number, inventory=None):
        """Delete an item from storage (and the inventory, if supplied).

        Returns True if the item existed in the database.
        """
        serial_number = str(serial_number)
        deleted = self.repository.delete(serial_number)
        if inventory is not None:
            # Inventory.remove_item expects an Item object, not a serial number.
            existing = inventory.search_item_by_serial(serial_number)
            if existing is not None:
                inventory.remove_item(existing)
        return deleted

    # ----- read / search -----

    def get_all_items(self):
        """Return all items stored in the database."""
        return self.repository.read_all()

    def get_item(self, serial_number):
        """Return one item, or None if it does not exist."""
        return self.repository.read_by_serial(serial_number)

    def search_items(self, keyword):
        """Search stored items by name or serial number."""
        return self.repository.search(keyword)

    def filter_items_by_status(self, status):
        """Filter stored items by their status."""
        return self.repository.filter_by_status(status)

    # ----- loading / maintenance -----

    def load_inventory(self):
        """Load database records into the in-memory Inventory object."""
        inventory = Inventory()
        for item in self.get_all_items():
            inventory.add_item(item)
        return inventory

    def refresh_stored_status(self, inventory):
        """Write today's days_remaining and status back to the database.

        Item recalculates both values whenever it is built, but the stored
        columns (used by filter_items_by_status) would otherwise go stale.
        """
        self.repository.update_calculated_fields(inventory.get_items())

    def save_inventory(self, inventory):
        """Make the database match the in-memory Inventory.

        Lets layers that only change the Inventory (add_item / remove_item /
        item.update) persist their work with a single call.
        """
        self.repository.sync(inventory.get_items())

    def is_csv_imported(self):
        """True once the legacy CSV has been imported (or deliberately skipped)."""
        return self.repository.get_meta("csv_imported") == "1"

    def mark_csv_imported(self):
        self.repository.set_meta("csv_imported", "1")

    def close(self):
        """Release the repository's database connection."""
        self.repository.close()
