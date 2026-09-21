#imports
from rich.console import Console 
from rich.table import Table

#terminal_UI
print("╔════════════════════════════════════════════╗")
print("║     🤖 Welcome to G6 food waste tracker   ║ ")
print("║                                            ║")
print("║  📦 Inventory:  xx items                   ║")
print("║  ⚠️  Expiring:   xx items                  ║")
print("║  🗑️  Wasted:     xx items                  ║")
print("╚════════════════════════════════════════════╝")

datatable = Table(title = "Food Inventory")

datatable.add_column("Food Name", justify="center", style="cyan",   no_wrap=True)
datatable.add_column("Expiry_Date", style="magenta")
datatable.add_column("Category", justify="center", style="green")
datatable.add_column("Date_Purchased", justify="center", style="green")
datatable.add_column("Inventory_Quantity", justify="center", style="green")

datatable.add_row("Chicken", "Milk", "Orange")
datatable.add_row("20/10/2027", "24/12/2028", "30/12/2027")
datatable.add_row("", "", "")
datatable.add_row("", "", "")
datatable.add_row("", "", "")

console = Console()
console.print(datatable)
