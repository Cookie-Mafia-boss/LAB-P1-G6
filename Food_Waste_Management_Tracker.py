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
    datatable.add_column("Expiry_Date", style="magenta")
    datatable.add_column("Category", justify="center", style="bright_yellow")
    datatable.add_column("Date_Purchased", justify="center", style="deep_pink4")
    datatable.add_column("Inventory_Quantity", justify="center", style="blue3")

    #this is the data rows
    datatable.add_row("chicken", "25/04/2029", "")
    datatable.add_row("milk", "25/04/2029", "")
    datatable.add_row("orange", "25/04/2029", "")
    datatable.add_row("", "", "")
    datatable.add_row("", "", "")

    #display the datatable
    console = Console()
    console.print(datatable)

    return(datatable)

print(food_inventory_table())





