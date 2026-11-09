import ctypes
import os
from datetime import datetime
from rich import print
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.console import Console
from rich.text import Text

#from classes.inventory import Inventory
from classes.item import Item
from logic_layer import validate_expiry_date, validate_food_name, validate_qty

DATE_FORMAT = "%d/%m/%Y"
console = Console()

# ==========================================
# NEW AI RESPONSE RENDERING (Pydantic model)
# ==========================================

def display_ai_response(response):
    """Render an AISuggestionResponse (from ai_service / ai_data_validation).

    Schema (confirmed via classes/ai_prompt.py):
        response.items[*] : food_name, waste_risk_level, days_remaining,
                            recommended_action
        response.waste_trend_summary       : str
        response.resupply_recommendations  : str
        response.recipe_suggestions        : list[str]
    """
    items = getattr(response, "items", None) or []

    if not items:
        console.print(Panel(
            "[dim]No AI suggestions available (empty inventory "
            "or safe default returned by ai_service).[/dim]",
            title="AI Suggestions", border_style="dim",
        ))
        return

    console.print(Panel(
        Text("AI Food-Waste Suggestions", style="bold cyan", justify="center"),
        border_style="cyan", padding=(0, 1),
    ))

    # --- per-item table ------------------------------------------------
    table = Table(show_header=True, header_style="bold purple")
    table.add_column("Item", style="bold")
    table.add_column("Days Left", justify="center")
    table.add_column("Waste Risk", justify="center")
    table.add_column("Recommended Action", overflow="fold")

    risk_colour = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}

    for row in items:
        risk = (row.waste_risk_level or "").upper()
        risk_fmt = (
            f"[bold {risk_colour[risk]}]{risk}[/bold {risk_colour[risk]}]"
            if risk in risk_colour else risk
        )

        action = row.recommended_action or ""
        action_fmt = (
            f"[bold red]{action}[/bold red]"
            if action.startswith("CRITICAL") else action
        )

        table.add_row(
            row.food_name,
            str(row.days_remaining),
            risk_fmt,
            action_fmt,
        )

    console.print(table)

    # --- top-level narrative sections ---------------------------------
    if getattr(response, "waste_trend_summary", ""):
        console.print(Panel(
            Markdown(_safe(response.waste_trend_summary)),
            title="Waste Trend Summary",
            border_style="blue", title_align="left",
        ))

    if getattr(response, "resupply_recommendations", ""):
        console.print(Panel(
            Markdown(_safe(response.resupply_recommendations)),
            title="Resupply Recommendations",
            border_style="magenta", title_align="left",
        ))

    recipes = getattr(response, "recipe_suggestions", None) or []
    if recipes:
        body = "\n".join(f"- {_safe(r)}" for r in recipes)
        console.print(Panel(
            Markdown(body),
            title="Recipe Suggestions",
            border_style="green", title_align="left",
        ))


def display_inventory_stats(inventory):
    """Quick stats — corrected for the current Item/Inventory classes."""
    items = inventory.get_items()
    total = len(items)
    expired = sum(1 for i in items if i.status == "EXPIRED")
    expiring = sum(1 for i in items if i.status == "EXPIRING")
    fresh = total - expired - expiring

    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column(style="bold")
    stats.add_column(justify="right")
    stats.add_row("Total Items", str(total))
    stats.add_row("[red]Expired[/red]", str(expired))
    stats.add_row("[yellow]Expiring Soon[/yellow]", str(expiring))
    stats.add_row("[green]Fresh[/green]", str(fresh))

    console.print(Panel(stats, title="Quick Stats",
                        border_style="dim cyan", padding=(1, 2)))


def _safe(text: str) -> str:
    """Windows-cp1252-safe encoding (mirrors _create_panel)."""
    return text.encode("cp1252", errors="replace").decode("cp1252")


# ==========================================
# PRESENTATION / DISPLAY FUNCTIONS
# ==========================================

def display_items(inventory, title):
    """Display inventory as a formatted table."""
    table = Table(title=title, show_header=True, header_style="bold purple")
    table.add_column("Serial Number", no_wrap=True)
    table.add_column("Food Name", justify="center")
    table.add_column("Qty", style="cyan", justify="center")
    table.add_column("Expiry Date", style="cyan", justify="center")
    table.add_column("Days Left", style="cyan", justify="center")
    table.add_column("Status", justify="right")

    for item in inventory.get_items():
        raw_status = item.status
        if raw_status == "EXPIRED":
            status_formatted = "[bold red]EXPIRED[/bold red]"
        elif raw_status == "EXPIRING":
            status_formatted = "[bold yellow]EXPIRING[/bold yellow]"
        elif raw_status == "FRESH":
            status_formatted = "[bold green]FRESH[/bold green]"
        else:
            status_formatted = raw_status

        table.add_row(
            item.serial_number,
            item.food_name,
            str(item.inventory_quantity),
            item.expiry_date,
            str(item.days_remaining),
            status_formatted
        )
    return table

def sort_expiring_items(expiring_inventory):
    """Return a list of expiring items sorted by days remaining."""
    return sorted(expiring_inventory, key=lambda x: x.days_remaining())

def display_ai_suggestions(sections):
    """
    Display AI response as structured panels with colors.
    sections: dict with keys 'recipes', 'waste_trends', 'immediate_action', 'resupply'
    """
    if not sections or "error" in sections:
        error_msg = sections.get("error", "Unknown error") if sections else "No response"
        console.print(Panel(
            f"[bold red]Error calling Gemini API:[/bold red]\n{error_msg}",
            title="AI Error",
            border_style="red"
        ))
        return

    # Create panels for each section (only non-empty)
    panels = []
    for title, content, color in [
        ("Recipes to Prioritize", sections.get("recipes", ""), "green"),
        ("Waste Trends", sections.get("waste_trends", ""), "blue"),
        ("Immediate Action Required", sections.get("immediate_action", ""), "red"),
        ("Resupply Recommendations", sections.get("resupply", ""), "magenta"),
    ]:
        if content.strip():
            panels.append(_create_panel(title, content, color))

    if not panels:
        console.print(Panel("[dim]No suggestions available[/dim]", border_style="dim"))
        return

    # Header
    console.print()
    console.print(Panel(
        Text("AI Recipe & Waste Prevention Suggestions", style="bold cyan", justify="center"),
        border_style="cyan",
        padding=(0, 1)
    ))

    # Panels
    for panel in panels:
        console.print(panel)
        console.print()


def display_ai_summary_stats(inventory, expiring_items):
    """Show quick stats table at bottom."""
    total = len(inventory)
    expired = sum(1 for item in inventory if item['Status'] == 'EXPIRED')
    expiring = len(expiring_items)
    fresh = total - expired - expiring

    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column(style="bold")
    stats.add_column(justify="right")
    stats.add_row("Total Items", str(total))
    stats.add_row("[red]Expired[/red]", str(expired))
    stats.add_row("[yellow]Expiring Soon[/yellow]", str(expiring))
    stats.add_row("[green]Fresh[/green]", str(fresh))

    console.print(Panel(stats, title="Quick Stats", border_style="dim cyan", padding=(1, 2)))


def _create_panel(title: str, content: str, border_style: str) -> Panel:
    """Create a styled panel with Windows-safe encoding."""
    safe_content = content.encode('cp1252', errors='replace').decode('cp1252')
    return Panel(
        Markdown(safe_content) if safe_content.strip() else "[dim]No data available[/dim]",
        title=title,
        title_align="left",
        border_style=border_style,
        padding=(1, 2),
        expand=True
    )


def raise_alert(expiring_inventory):
    if expiring_inventory is not None:
        expire_alert(expiring_inventory)


def do_nothing():
    print("User clicked No.")


def expire_alert(inventory):
    if inventory is None:
        return  # No alert if no expiring items

    alert_title = "Items are about to expire!"
    alert_text = f"{inventory.get_length()} item(s) are about to expire! Would you like to view them?"

    if os.name == 'nt':
        result = ctypes.windll.user32.MessageBoxW(0, alert_text, alert_title, 4)
        if result == 6:
            print(display_items(inventory, "Expiring Items"))
        elif result == 7:
            do_nothing()
    else:
        choice = input(f"\n[Warning] {alert_text} (y/n): ").strip().lower()
        if choice == 'y':
            print(display_items(inventory, "Expiring Items"))
        else:
            do_nothing()

def check_expires(inventory):
    try:
        days = input("Enter warning threshold in days [Default: 30]: ").strip()
        days = int(days) if days else 30
    except ValueError:
        days = 30
    expiring = inventory.expiring_items_within_days(alert_days=days)
    if expiring is not None and expiring.get_length() > 0:
        print(display_items(expiring, f"Items Expiring Within {days} Days"))
    else:
        print(f"✅ No items expiring within {days} days.")

# def add_food_item(inventory):
#     """Stub function to allow adding items manually."""
#     print("\n--- Add New Food Item ---")
#     serial_num = len(inventory) + 1
#     serial_num_str = f"{str(serial_num).zfill(4)}"

#     # Reject the item if the food name is empty or purely numeric
#     name, error = validate_food_name(input("Enter food name: "))
#     if error:
#         print(f"[red]Error:[/red] {error}")
#         return
     
#     qty_input = input("Enter quantity: ").strip()

#     qty, error = validate_qty(qty_input)
#     if error:
#         print(f"[red]Error:[/red] {error}")
#         return

#     exp_date = input(f"Enter expiry date ({DATE_FORMAT}): ").strip()

#     # Reject the item if the expiry date is invalid or more than MAX_YEARS away
#     exp_dt, error = validate_expiry_date(exp_date)
#     if error:
#         print(f"[red]Error:[/red] {error}")
#         return

#     purch_date = datetime.now().strftime(DATE_FORMAT)

#     try:
#         days_rem = (exp_dt - datetime.now().date()).days
#         if days_rem <= 0:
#             status = "EXPIRED"
#         elif days_rem <= 30:
#             status = "EXPIRING"
#         else:
#             status = "FRESH"

#         inventory.append({
#             "Serial_Number": serial_num_str,
#             "Food_Name": name,
#             "Expiry_Date": exp_date,
#             "Date_Purchased": purch_date,
#             "Inventory_Quantity": int(qty),
#             "Days_Remaining": days_rem,
#             "Status": status
#         })

#         print(f"[green]Success:[/green] Added '{name}' successfully!")

#     except Exception as e:
#         print(f"[red]Error:[/red] Failed to add item: {e}")

def add_food_item(inventory):
    """Add a new food item to the inventory manually."""
    print("\n--- Add New Food Item ---")

    # Next serial number: highest existing + 1, so removing items never causes duplicates
    existing = [int(item.serial_number) for item in inventory.get_items()]
    serial_num_str = str(max(existing, default=0) + 1).zfill(4)

    name, error = validate_food_name(input("Enter food name: "))
    if error:
        print(f"[red]Error:[/red] {error}")
        return

    qty, error = validate_qty(input("Enter quantity: ").strip())
    if error:
        print(f"[red]Error:[/red] {error}")
        return

    exp_date = input(f"Enter expiry date ({DATE_FORMAT}): ").strip()
    exp_dt, error = validate_expiry_date(exp_date)
    if error:
        print(f"[red]Error:[/red] {error}")
        return

    purch_date = datetime.now().strftime(DATE_FORMAT)

    try:
        item = Item(serial_num_str, name, exp_date, purch_date, int(qty))
        inventory.add_item(item)
        print(f"[green]Success:[/green] Added '{name}' successfully!")
    except Exception as e:
        print(f"[red]Error:[/red] Failed to add item: {e}")


def _renumber_serial_numbers(inventory):
    """Renumber serial numbers sequentially (0001, 0002, ...) after deletion."""
    for index, item in enumerate(inventory, start=1):
        item["Serial_Number"] = f"{str(index).zfill(4)}"


# def delete_food_item(inventory):
#     serial_number = input("Input Serial Number to delete: ")
#     found = False
#     for item in inventory:
#         if item["Serial_Number"] == serial_number:
#             found = True
#             inventory.remove(item)

#     if found:
#         # Renumber remaining items to maintain sequential order
#         _renumber_serial_numbers(inventory)
#         print("\nItem successfully deleted")
#     else:
#         print("\nSerial Number not found")

def delete_food_item(inventory):
    serial_number = input("Input Serial Number to delete: ")
    item = inventory.search_item_by_serial(serial_number)
    if item is None:
        print("\nSerial Number not found")
        return
    
    inventory.remove_item(item)
    print("\nItem successfully deleted")
            

# def update_food_item(inventory):
#     serial_number = input("Input Serial Number to update: ")
#     found = False
#     for item in inventory:
#         if item["Serial_Number"] == serial_number:
#             found = True
#             name, error = validate_food_name(input("Enter food name: "))
#             if error:
#                 print(f"[red]Error:[/red] {error}")
#                 return
            
#             qty_input = input("Enter quantity: ").strip()
#             qty, error = validate_qty(qty_input)
#             if error:
#                 print(f"[red]Error:[/red] {error}")
#                 return


#             exp_date = input(f"Enter expiry date ({DATE_FORMAT}): ").strip()
#             exp_dt, error = validate_expiry_date(exp_date)
#             if error:
#                 print(f"[red]Error:[/red] {error}")
#                 return
            
#             purch_date = datetime.now().strftime(DATE_FORMAT)
#             try:
#                     exp_dt = datetime.strptime(exp_date, DATE_FORMAT).date()
#                     days_rem = (exp_dt - datetime.now().date()).days
#                     if days_rem <= 0:
#                         status = "EXPIRED"
#                     elif days_rem <= 30:
#                         status = "EXPIRING"
#                     else:
#                         status = "FRESH"
#             except Exception as e:
#                     print(f"[red]Error:[/red] Failed to update item: {e}")

#             item["Food_Name"] = name
#             item["Expiry_Date"] = exp_date
#             item["Date_Purchased"] = purch_date
#             item["Inventory_Quantity"] = int(qty)
#             item["Days_Remaining"] = days_rem
#             item["Status"] = status
 

#     if found != True:
#         print("Item not found")
#     else:
#         print("\nItem updated")

def update_food_item(inventory):
    """Update an existing food item in the inventory."""
    serial_number = input("Input Serial Number to update: ").strip().zfill(4)

    item = inventory.search_item_by_serial(serial_number)
    if item is None:
        print("Item not found")
        return

    name, error = validate_food_name(input("Enter food name: "))
    if error:
        print(f"[red]Error:[/red] {error}")
        return

    qty, error = validate_qty(input("Enter quantity: ").strip())
    if error:
        print(f"[red]Error:[/red] {error}")
        return

    exp_date = input(f"Enter expiry date ({DATE_FORMAT}): ").strip()
    exp_dt, error = validate_expiry_date(exp_date)
    if error:
        print(f"[red]Error:[/red] {error}")
        return

    purch_date = datetime.now().strftime(DATE_FORMAT)

    try:
        item.update(name, exp_date, purch_date, int(qty))
        print("\nItem updated")
    except Exception as e:
        print(f"[red]Error:[/red] Failed to update item: {e}")