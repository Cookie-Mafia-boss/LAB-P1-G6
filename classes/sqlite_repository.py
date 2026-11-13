"""SQLite implementation of the DataRepository interface."""

import sqlite3
from pathlib import Path

from classes.data_exceptions import (
    DatabaseConnectionError,
    DuplicateRecordError,
    RecordNotFoundError,
)
from classes.data_repository import DataRepository
from classes.item import Item


class SQLiteRepository(DataRepository):
    """Performs CRUD and search operations using an SQLite database."""

    def __init__(self, database_path):
        self.database_path = str(database_path)
        try:
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row
            self._create_table()
        except sqlite3.Error as error:
            raise DatabaseConnectionError(
                f"Could not open database: {error}"
            ) from error

    def _create_table(self):
        """Create the food_items table if it does not already exist."""
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS food_items (
                serial_number TEXT PRIMARY KEY,
                food_name TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                date_purchased TEXT NOT NULL,
                inventory_quantity INTEGER NOT NULL,
                days_remaining INTEGER,
                status TEXT
            )
            """
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS app_meta "
            "(key TEXT PRIMARY KEY, value TEXT)"
        )
        self.connection.commit()

    @staticmethod
    def _row_to_item(row):
        """Convert a database row into an Item object."""
        if row is None:
            return None
        # Item calculates days_remaining and status itself from the expiry
        # date, so the stored copies of those two columns are not read back.
        return Item(
            serial_number=row["serial_number"],
            food_name=row["food_name"],
            expiry_date=row["expiry_date"],
            date_purchased=row["date_purchased"],
            inventory_quantity=row["inventory_quantity"],
        )

    def create(self, item):
        """Insert a new item; duplicate serial numbers raise an exception."""
        try:
            self.connection.execute(
                """
                INSERT INTO food_items
                (serial_number, food_name, expiry_date, date_purchased,
                 inventory_quantity, days_remaining, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item.serial_number), item.food_name, str(item.expiry_date),
                    str(item.date_purchased), int(item.inventory_quantity),
                    item.days_remaining, item.status,
                ),
            )
            self.connection.commit()
            return item
        except sqlite3.IntegrityError as error:
            raise DuplicateRecordError(
                f"Serial number {item.serial_number} already exists."
            ) from error
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database insert failed: {error}") from error

    def read_all(self):
        """Read all food items, ordered by serial number."""
        try:
            rows = self.connection.execute(
                "SELECT * FROM food_items ORDER BY serial_number"
            ).fetchall()
            return [self._row_to_item(row) for row in rows]
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database read failed: {error}") from error

    def read_by_serial(self, serial_number):
        """Read one food item using its serial number."""
        try:
            row = self.connection.execute(
                "SELECT * FROM food_items WHERE serial_number = ?",
                (str(serial_number),),
            ).fetchone()
            return self._row_to_item(row)
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database lookup failed: {error}") from error

    def update(self, item):
        """Update an existing item; raise if the serial number is not found."""
        try:
            cursor = self.connection.execute(
                """
                UPDATE food_items
                SET food_name = ?, expiry_date = ?, date_purchased = ?,
                    inventory_quantity = ?, days_remaining = ?, status = ?
                WHERE serial_number = ?
                """,
                (
                    item.food_name, str(item.expiry_date), str(item.date_purchased),
                    int(item.inventory_quantity), item.days_remaining, item.status,
                    str(item.serial_number),
                ),
            )
            self.connection.commit()
            if cursor.rowcount == 0:
                raise RecordNotFoundError(
                    f"Serial number {item.serial_number} was not found."
                )
            return item
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database update failed: {error}") from error

    def update_calculated_fields(self, items):
        """Write days_remaining and status for many items in one transaction."""
        try:
            self.connection.executemany(
                "UPDATE food_items SET days_remaining = ?, status = ? "
                "WHERE serial_number = ?",
                [
                    (item.days_remaining, item.status, str(item.serial_number))
                    for item in items
                ],
            )
            self.connection.commit()
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database refresh failed: {error}") from error

    def sync(self, items):
        """Make the database match ``items`` exactly, in one transaction."""
        items = list(items)
        try:
            with self.connection:  # commits on success, rolls back on error
                self.connection.executemany(
                    """
                    INSERT INTO food_items
                    (serial_number, food_name, expiry_date, date_purchased,
                     inventory_quantity, days_remaining, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(serial_number) DO UPDATE SET
                        food_name = excluded.food_name,
                        expiry_date = excluded.expiry_date,
                        date_purchased = excluded.date_purchased,
                        inventory_quantity = excluded.inventory_quantity,
                        days_remaining = excluded.days_remaining,
                        status = excluded.status
                    """,
                    [
                        (
                            str(i.serial_number), i.food_name, str(i.expiry_date),
                            str(i.date_purchased), int(i.inventory_quantity),
                            i.days_remaining, i.status,
                        )
                        for i in items
                    ],
                )
                keep = {str(i.serial_number) for i in items}
                stored = [
                    r[0] for r in self.connection.execute(
                        "SELECT serial_number FROM food_items"
                    )
                ]
                self.connection.executemany(
                    "DELETE FROM food_items WHERE serial_number = ?",
                    [(s,) for s in stored if s not in keep],
                )
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database sync failed: {error}") from error

    def get_meta(self, key):
        """Return a stored setting value, or None."""
        try:
            row = self.connection.execute(
                "SELECT value FROM app_meta WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else None
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database read failed: {error}") from error

    def set_meta(self, key, value):
        """Store a setting value."""
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO app_meta (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, str(value)),
                )
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database write failed: {error}") from error

    def delete(self, serial_number):
        """Delete an item by serial number."""
        try:
            cursor = self.connection.execute(
                "DELETE FROM food_items WHERE serial_number = ?",
                (str(serial_number),),
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database delete failed: {error}") from error

    def renumber_serial_numbers(self):
        """
        Renumber all serial numbers sequentially (1, 2, 3...) based on current order.

        Returns the number of items renumbered.
        """
        try:
            # Get all items in current order (ordered by serial_number)
            rows = self.connection.execute(
                "SELECT serial_number FROM food_items ORDER BY serial_number"
            ).fetchall()

            if not rows:
                return 0

            # Update each item with new sequential serial number
            with self.connection:
                for index, row in enumerate(rows, start=1):
                    old_serial = row["serial_number"]
                    new_serial = str(index).zfill(4)
                    if old_serial != new_serial:
                        self.connection.execute(
                            "UPDATE food_items SET serial_number = ? WHERE serial_number = ?",
                            (new_serial, old_serial),
                        )
            return len(rows)
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database renumber failed: {error}") from error

    def search(self, keyword):
        """Find items whose name or serial number contains the keyword."""
        try:
            pattern = f"%{keyword}%"
            rows = self.connection.execute(
                """
                SELECT * FROM food_items
                WHERE food_name LIKE ? OR serial_number LIKE ?
                ORDER BY food_name
                """,
                (pattern, pattern),
            ).fetchall()
            return [self._row_to_item(row) for row in rows]
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database search failed: {error}") from error

    def filter_by_status(self, status):
        """Return all items with the requested status."""
        try:
            rows = self.connection.execute(
                "SELECT * FROM food_items WHERE status = ? ORDER BY expiry_date",
                (status,),
            ).fetchall()
            return [self._row_to_item(row) for row in rows]
        except sqlite3.Error as error:
            raise DatabaseConnectionError(f"Database filter failed: {error}") from error

    def close(self):
        """Close the SQLite connection."""
        if self.connection:
            self.connection.close()
