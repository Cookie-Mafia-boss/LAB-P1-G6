import datetime

class Item():
    def __init__(self, serial_number, food_name, expiry_date, date_purchased, inventory_quantity):
        self.__serial_number = serial_number
        self.__food_name = food_name
        self.__expiry_date = expiry_date
        self.__date_purchased = date_purchased
        self.__inventory_quantity = inventory_quantity
        self.__days_remaining = self.calculate_days_remaining()
        self.__status = self.determine_status()

    @property
    def serial_number(self):
        return self.__serial_number

    @property
    def food_name(self):
        return self.__food_name

    @property
    def expiry_date(self):
        return self.__expiry_date

    @property
    def date_purchased(self):
        return self.__date_purchased

    @property
    def inventory_quantity(self):
        return self.__inventory_quantity

    @property
    def days_remaining(self):
        return self.__days_remaining

    @property
    def status(self):
        return self.__status

    def calculate_days_remaining(self):
        today = datetime.datetime.now().date()
        exp_date = datetime.datetime.strptime(self.__expiry_date, "%d/%m/%Y").date()
        return (exp_date - today).days

    def determine_status(self):
        if self.__days_remaining <= 0:
            return "EXPIRED"
        elif self.__days_remaining <= 30:
            return "EXPIRING"
        else:
            return "FRESH"

    def display_info(self):
        print (f"Serial Number: {self.__serial_number}, "
                f"Food Name: {self.__food_name}, "
                f"Expiry Date: {self.__expiry_date}, "
                f"Date Purchased: {self.__date_purchased}, "
                f"Inventory Quantity: {self.__inventory_quantity}, "
                f"Days Remaining: {self.__days_remaining}, "
                f"Status: {self.__status}")

    def update(self, food_name, expiry_date, date_purchased, inventory_quantity):
        self.__food_name = food_name
        self.__expiry_date = expiry_date
        self.__date_purchased = date_purchased
        self.__inventory_quantity = inventory_quantity
        # Recalculate in this order: status depends on days_remaining
        self.__days_remaining = self.calculate_days_remaining()
        self.__status = self.determine_status()