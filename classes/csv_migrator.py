"""One-time utility for importing the original CSV into SQLite."""

import csv
from datetime import datetime

from classes.data_exceptions import DataValidationError, DuplicateRecordError
from classes.item import Item


class CSVMigrator:
    """Reads the legacy CSV format and inserts its rows through DataManager."""

    EXPECTED_COLUMNS = {
        "Serial_Number",
        "Food_Name",
        "Expiry_Date",
        "Date_Purchased",
        "Inventory_Quantity",
    }
    # Days_Remaining and Status may still be present in the CSV, but Item
    # recalculates them from the expiry date, so they are not required.

    def __init__(self, data_manager, date_format="%d/%m/%Y"):
        self.data_manager = data_manager
        self.date_format = date_format

    @staticmethod
    def _normalise(name):
        """'Food Name' / ' Food_Name ' -> 'Food_Name'."""
        return name.strip().replace(" ", "_")

    def migrate(self, csv_path, skip_duplicates=True):
        """Import CSV rows.

        Returns {"imported": n, "skipped": n, "errors": [messages]}.
        Rows that are blank, have a bad date/quantity, or repeat a serial
        number are skipped (and reported) rather than aborting the import.
        """
        imported = 0
        skipped = 0
        errors = []

        try:
            with open(csv_path, "r", newline="", encoding="utf-8-sig") as csv_file:
                reader = csv.DictReader(csv_file)
                if reader.fieldnames:
                    reader.fieldnames = [self._normalise(f) for f in reader.fieldnames if f is not None]
                if not reader.fieldnames or not self.EXPECTED_COLUMNS.issubset(
                    set(reader.fieldnames)
                ):
                    raise DataValidationError(
                        "CSV is missing one or more expected column headers."
                    )

                for line_number, raw in enumerate(reader, start=2):
                    row = {k: (v or "").strip() for k, v in raw.items() if k}
                    if not all(row.get(c) for c in self.EXPECTED_COLUMNS):
                        skipped += 1
                        errors.append(f"Line {line_number}: missing value(s)")
                        continue
                    try:
                        expiry = datetime.strptime(row["Expiry_Date"], self.date_format).date()
                        purchased = datetime.strptime(row["Date_Purchased"], self.date_format).date()
                        item = Item(
                            serial_number=row["Serial_Number"],
                            food_name=row["Food_Name"],
                            expiry_date=expiry.strftime(self.date_format),
                            date_purchased=purchased.strftime(self.date_format),
                            inventory_quantity=int(row["Inventory_Quantity"]),
                        )
                        self.data_manager.add_item(item)
                        imported += 1
                    except DuplicateRecordError:
                        skipped += 1
                        errors.append(f"Line {line_number}: duplicate serial {row['Serial_Number']}")
                        if not skip_duplicates:
                            raise
                    except (ValueError, TypeError) as error:
                        skipped += 1
                        errors.append(f"Line {line_number}: {error}")
        except OSError as error:
            raise DataValidationError(f"Could not read CSV file: {error}") from error

        return {"imported": imported, "skipped": skipped, "errors": errors}
