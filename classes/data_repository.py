"""Abstract interface defining the database operations.""" 

from abc import ABC, abstractmethod


class DataRepository(ABC):
    """Defines the operations any concrete data repository must provide.

    DataManager depends on this interface rather than on SQLite directly.
    This makes it possible to replace SQLite with another storage system.
    """

    @abstractmethod
    def create(self, item):
        """Insert a new item and return it."""
        raise NotImplementedError

    @abstractmethod
    def read_all(self):
        """Return every stored item."""
        raise NotImplementedError

    @abstractmethod
    def read_by_serial(self, serial_number):
        """Return one item by serial number, or None."""
        raise NotImplementedError

    @abstractmethod
    def update(self, item):
        """Update an existing item and return it."""
        raise NotImplementedError

    @abstractmethod
    def update_calculated_fields(self, items):
        """Store the freshly calculated days_remaining and status of items."""
        raise NotImplementedError

    @abstractmethod
    def sync(self, items):
        """Make the stored records exactly match ``items`` (one transaction).

        Items not yet stored are inserted, stored items are updated, and
        stored records that are not in ``items`` are deleted.
        """
        raise NotImplementedError

    @abstractmethod
    def get_meta(self, key):
        """Return a stored setting (e.g. a migration flag), or None."""
        raise NotImplementedError

    @abstractmethod
    def set_meta(self, key, value):
        """Store a small setting value."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, serial_number):
        """Delete an item; return True if it existed."""
        raise NotImplementedError

    @abstractmethod
    def search(self, keyword):
        """Search item names and serial numbers."""
        raise NotImplementedError

    @abstractmethod
    def filter_by_status(self, status):
        """Return items matching a status."""
        raise NotImplementedError

    @abstractmethod
    def close(self):
        """Close resources held by the repository."""
        raise NotImplementedError
