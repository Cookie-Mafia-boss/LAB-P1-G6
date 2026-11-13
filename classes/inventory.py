class Inventory:
    def __init__(self):
        self.__items = []

    def add_item(self, item):
        self.__items.append(item)

    def remove_item(self, item):
        if item in self.__items:
            self.__items.remove(item)

    def search_item_by_serial(self, serial_number):
        for item in self.__items:
            if item.serial_number == serial_number:
                return item
        return None

    def get_items(self):
        return list(self.__items)

    def display_items(self):
        if len(self.__items) == 0:
            return "No items in inventory."
        for item in self.__items:
            item.display_info()

    def get_length(self):
        return len(self.__items)
    
    def expiring_items(self):
        result = Inventory()
        for item in self.__items:
            if item.status == "EXPIRING":
                result.add_item(item)
        return result

    def expiring_items_within_days(self, alert_days):
        result = Inventory()
        for item in self.__items:
            if 0 < item.days_remaining <= alert_days:
                result.add_item(item)
        return result