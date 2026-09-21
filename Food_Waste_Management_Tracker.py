#imports
from rich.console import Console 
from rich.table import Table

#terminal_UI
print("╔════════════════════════════════════════════╗")
print("║     🤖 Welcome to G6 food waste tracker    ║ ")
print("║                                            ║")
print("║  📦 Inventory:  xx items                   ║")
print("║  ⚠️  Expiring:   xx items                  ║")
print("║  🗑️  Wasted:     xx items                  ║")
print("╚════════════════════════════════════════════╝")

def food_inventory_table():
    #datatable 
    datatable = Table(title = "Food Inventory")

    #this is the data column
    datatable.add_column("Food Name", justify="center", style="cyan",   no_wrap=True)
    datatable.add_column("Expiry Date", style="magenta")
    datatable.add_column("Category", justify="center", style="bright_yellow")
    datatable.add_column("Date Purchased", justify="center", style="deep_pink4")
    datatable.add_column("Inventory_Quantity", justify="center", style="blue3")

    #store user_input into variables 
    Food_Name = input("Food_Name : ")
    Expiry_Date = input("Expiry Date : ")
    Category = input("Category : ")
    Date_Purchased = input("Date Purchased : ")
    Inventory_Quantity = input("Inventory Quantity : ")

    #this is the data column
    datatable.add_row(Food_Name,Expiry_Date, Category, Date_Purchased, Inventory_Quantity)
    
    

    #display the datatable
    console = Console()
    console.print(datatable)

   

    return(datatable)

print(food_inventory_table())

#use difflib()
def data_Validator():

    return




