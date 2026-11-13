"""
Input/Output Layer - All UI, display, and user interaction functions.

This module contains ALL presentation logic:
- Rich console display functions (tables, panels, markdown)
- User input prompts and validation
- Menu rendering and navigation
- Alert dialogs (Windows message box + console fallback)
- AI suggestion display formatting
"""

import ctypes
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from rich import print
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, Confirm

from classes.inventory import Inventory
from classes.item import Item
from logic_layer import validate_expiry_date, validate_food_name, validate_qty
from data_layer import get_data_manager, save_inventory

DATE_FORMAT = "%d/%m/%Y"
console = Console()


# ==========================================
# CORE DISPLAY FUNCTIONS
# ==========================================

def display_items(inventory: Inventory, title: str) -> Table:
    """Display inventory as a formatted Rich table."""
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


def sort_expiring_items(expiring_inventory: Inventory) -> List[Item]:
    """Return a list of expiring items sorted by days remaining."""
    return sorted(expiring_inventory.get_items(), key=lambda x: x.days_remaining)


# ==========================================
# AI DISPLAY FUNCTIONS
# ==========================================

def display_ai_suggestions(sections: Dict[str, str]) -> None:
    """
    Display AI response as structured panels with colors.
    sections: dict with keys 'recipes', 'waste_trends', 'immediate_action', 'resupply'
    """
    if not sections or "error" in sections:
        error_msg = sections.get("error", "Unknown error") if sections else "No response"
        console.print(Panel(
            f"[bold red]Error calling AI:[/bold red]\n{error_msg}",
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


def display_ai_item_analysis(items: List[Any]) -> None:
    """Display detailed AI analysis per item in a table."""
    console.print()

    table = Table(title="AI Item Analysis", show_header=True, header_style="bold magenta")
    table.add_column("Food Name", style="cyan")
    table.add_column("Risk Level", justify="center")
    table.add_column("Days Left", justify="center", style="yellow")
    table.add_column("Recommended Action")

    for item in items:
        risk_style = {"high": "red", "medium": "yellow", "low": "green"}.get(
            item.waste_risk_level.lower(), "white"
        )
        table.add_row(
            item.food_name,
            f"[{risk_style}]{item.waste_risk_level.upper()}[/{risk_style}]",
            str(item.days_remaining),
            item.recommended_action
        )

    console.print(table)


def display_ai_summary_stats(inventory: Inventory, expiring_items: List[Item]) -> None:
    """Show quick stats table at bottom."""
    items = inventory.get_items()
    total = len(items)
    expired = sum(1 for item in items if item.status == 'EXPIRED')
    expiring_count = len(expiring_items)
    fresh = total - expired - expiring_count

    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column(style="bold")
    stats.add_column(justify="right")
    stats.add_row("Total Items", str(total))
    stats.add_row("[red]Expired[/red]", str(expired))
    stats.add_row("[yellow]Expiring Soon[/yellow]", str(expiring_count))
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


# ==========================================
# ALERT FUNCTIONS
# ==========================================

def do_nothing() -> None:
    print("User clicked No.")


def expire_alert(inventory: Optional[Inventory]) -> None:
    """Show expiry alert via Windows message box or console fallback."""
    if inventory is None or inventory.get_length() == 0:
        return  # No alert if no expiring items

    alert_title = "Items are about to expire!"
    alert_text = f"{inventory.get_length()} item(s) are about to expire! Would you like to view them?"

    if os.name == 'nt':
        result = ctypes.windll.user32.MessageBoxW(0, alert_text, alert_title, 4)
        if result == 6:  # Yes
            console.print(display_items(inventory, "Expiring Items"))
        elif result == 7:  # No
            do_nothing()
    else:
        choice = input(f"\n[Warning] {alert_text} (y/n): ").strip().lower()
        if choice == 'y':
            console.print(display_items(inventory, "Expiring Items"))
        else:
            do_nothing()


def check_expires(inventory: Inventory) -> None:
    """Check for expiring items with customizable threshold."""
    try:
        days_input = Prompt.ask("Enter warning threshold in days", default="30")
        days = int(days_input) if days_input else 30
    except ValueError:
        days = 30

    expiring = inventory.expiring_items_within_days(alert_days=days)
    if expiring is not None and expiring.get_length() > 0:
        console.print(display_items(expiring, f"Items Expiring Within {days} Days"))
    else:
        print(f"✅ No items expiring within {days} days.")


def run_check_expires(inventory: Inventory) -> None:
    """Wrapper for check_expires to maintain consistent naming."""
    check_expires(inventory)


# ==========================================
# MENU RENDERING
# ==========================================

def show_banner(title: str, subtitle: str = "") -> None:
    """Display a styled banner."""
    text = Text()
    text.append(title, style="bold cyan")
    if subtitle:
        text.append(f"\n{subtitle}", style="dim")
    console.print(Panel(text, border_style="cyan", padding=(1, 2)))


def show_main_menu(current_time: str = None) -> None:
    """Display the main menu options."""
    if current_time is None:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    console.print()
    show_banner("FOOD WASTE MANAGEMENT SYSTEM", f"Current time: {current_time}")

    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    menu_table.add_column("Option", style="bold yellow", width=3)
    menu_table.add_column("Description", style="white")

    options = [
        ("1", "View Inventory"),
        ("2", "Add New Food Item"),
        ("3", "Delete Food Item"),
        ("4", "Update Food Item"),
        ("5", "Check Expiry Alerts"),
        ("6", "Search Inventory"),
        ("7", "Filter by Status"),
        ("8", "Get AI Suggestions (Recipes, Waste Trends, Actions, Resupply)"),
        ("9", "Exit"),
    ]

    for opt, desc in options:
        menu_table.add_row(opt, desc)

    console.print(menu_table)


def get_user_choice() -> str:
    """Get and validate user menu choice."""
    while True:
        choice = input("Select an option [1-9]: ")
        if int(choice) >= 1 and int(choice) <= 10:
            return choice


def show_error(message: str) -> None:
    """Display an error message in a red panel."""
    console.print(Panel(
        f"[bold red]{message}[/bold red]",
        title="Error",
        border_style="red"
    ))


def show_success(message: str) -> None:
    """Display a success message."""
    print(f"[green]{message}[/green]")


def show_warning(message: str) -> None:
    """Display a warning message."""
    print(f"[yellow]{message}[/yellow]")


def show_info(message: str) -> None:
    """Display an info message."""
    print(f"[cyan]{message}[/cyan]")


# ==========================================
# INPUT/INTERACTION FUNCTIONS
# ==========================================

def prompt_search_keyword() -> str:
    """Prompt user for search keyword."""
    return Prompt.ask("Enter search keyword (name or serial number)").strip()


def prompt_filter_status() -> str:
    """Prompt user for status filter."""
    return Prompt.ask(
        "Filter by status",
        choices=["FRESH", "EXPIRING", "EXPIRED"],
        default="EXPIRING"
    )


def prompt_food_name() -> str:
    """Prompt for food name with validation."""
    while True:
        name = Prompt.ask("Enter food name").strip()
        validated, error = validate_food_name(name)
        if error:
            show_error(error)
            continue
        return validated


def prompt_quantity() -> int:
    """Prompt for quantity with validation."""
    while True:
        qty_input = Prompt.ask("Enter quantity").strip()
        qty, error = validate_qty(qty_input)
        if error:
            show_error(error)
            continue
        return qty


def prompt_expiry_date() -> str:
    """Prompt for expiry date with validation."""
    while True:
        exp_date = Prompt.ask(f"Enter expiry date ({DATE_FORMAT})").strip()
        exp_dt, error = validate_expiry_date(exp_date)
        if error:
            show_error(error)
            continue
        return exp_date


def prompt_serial_number(action: str) -> str:
    """Prompt for serial number."""
    return Prompt.ask(f"Input Serial Number to {action}").strip().zfill(4)


def confirm_action(message: str) -> bool:
    """Ask for confirmation."""
    return Confirm.ask(message)


# ==========================================
# CRUD INTERACTION WRAPPERS
# ==========================================

def run_add_food_item(inventory: Inventory) -> bool:
    """
    Run the add food item interaction.
    Returns True if item was added successfully.
    """
    console.print()
    show_banner("Add New Food Item")

    # Next serial number: highest existing + 1
    existing = [int(item.serial_number) for item in inventory.get_items()]
    serial_num_str = str(max(existing, default=0) + 1).zfill(4)

    name = prompt_food_name()
    qty = prompt_quantity()
    exp_date = prompt_expiry_date()
    purch_date = datetime.now().strftime(DATE_FORMAT)

    try:
        item = Item(serial_num_str, name, exp_date, purch_date, qty)
        inventory.add_item(item)
        show_success(f"Added '{name}' successfully!")
        return True
    except Exception as e:
        show_error(f"Failed to add item: {e}")
        return False


def run_delete_food_item(inventory: Inventory) -> bool:
    """
    Run the delete food item interaction.
    Returns True if item was deleted successfully.
    """
    console.print()
    serial_number = prompt_serial_number("delete")

    item = inventory.search_item_by_serial(serial_number)
    if item is None:
        show_error("Serial Number not found")
        return False

    if confirm_action(f"Delete '{item.food_name}' (Serial: {serial_number})?"):
        # Delete from database
        data_manager = get_data_manager()
        data_manager.delete_item(serial_number, inventory)
        # Renumber remaining items sequentially (1, 2, 3...)
        data_manager.renumber_serial_numbers(inventory)
        # Save changes
        save_inventory(inventory)
        show_success("Item successfully deleted")
        return True
    else:
        show_info("Deletion cancelled")
        return False


def run_update_food_item(inventory: Inventory) -> bool:
    """
    Run the update food item interaction.
    Returns True if item was updated successfully.
    """
    console.print()
    serial_number = prompt_serial_number("update")

    item = inventory.search_item_by_serial(serial_number)
    if item is None:
        show_error("Item not found")
        return False

    console.print(f"[dim]Updating: {item.food_name} (Serial: {serial_number})[/dim]")

    name = prompt_food_name()
    qty = prompt_quantity()
    exp_date = prompt_expiry_date()
    purch_date = datetime.now().strftime(DATE_FORMAT)

    try:
        item.update(name, exp_date, purch_date, qty)
        show_success("Item updated")
        return True
    except Exception as e:
        show_error(f"Failed to update item: {e}")
        return False


def run_search_inventory(inventory: Inventory, data_manager) -> None:
    """Run the search inventory interaction."""
    console.print()
    keyword = prompt_search_keyword()
    if not keyword:
        show_warning("Search keyword cannot be empty.")
        return

    results = data_manager.search_items(keyword)

    if results:
        temp_inv = Inventory()
        for item in results:
            temp_inv.add_item(item)
        console.print(display_items(temp_inv, f"Search Results for '{keyword}'"))
    else:
        show_info(f"No items found matching '{keyword}'.")


def run_filter_by_status(inventory: Inventory, data_manager) -> None:
    """Run the filter by status interaction."""
    console.print()
    status = prompt_filter_status()

    results = data_manager.filter_items_by_status(status)

    if results:
        temp_inv = Inventory()
        for item in results:
            temp_inv.add_item(item)
        console.print(display_items(temp_inv, f"Items with Status: {status}"))
    else:
        show_info(f"No items with status '{status}'.")


def run_ai_suggestions(inventory: Inventory, ai_service) -> None:
    """Run the AI suggestions interaction."""
    console.print()
    show_info("Analyzing inventory with AI...")

    ai_inventory = inventory_to_ai_format(inventory)

    if not ai_inventory:
        show_warning("Inventory is empty. Add some items first!")
        return

    try:
        response = ai_service.process_inventory(ai_inventory)

        # Convert Pydantic response to dict format for display
        sections = {
            "recipes": "\n".join(f"• {recipe}" for recipe in response.recipe_suggestions) if response.recipe_suggestions else "",
            "waste_trends": response.waste_trend_summary,
            "immediate_action": "\n".join(
                f"• {item.food_name} ({item.days_remaining}d left): {item.recommended_action}"
                for item in response.items if item.waste_risk_level.lower() == "high"
            ) if response.items else "",
            "resupply": response.resupply_recommendations,
        }

        display_ai_suggestions(sections)

        # Also show the detailed item analysis
        if response.items:
            display_ai_item_analysis(response.items)

    except Exception as e:
        show_error(f"AI Analysis Failed: {str(e)}")


def run_view_stats(inventory: Inventory) -> None:
    """Run the view statistics interaction."""
    console.print()
    expiring = inventory.expiring_items()
    display_ai_summary_stats(inventory, expiring.get_items() if expiring else [])


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def inventory_to_ai_format(inventory: Inventory) -> List[Dict[str, Any]]:
    """Convert Inventory items to the format expected by AI layer."""
    items = []
    for item in inventory.get_items():
        items.append({
            "Food_Name": item.food_name,
            "Expiry_Date": item.expiry_date,
            "Inventory_Quantity": item.inventory_quantity,
            "Days_Remaining": item.days_remaining,
            "Status": item.status,
        })
    return items


def show_startup_alert(inventory: Inventory) -> None:
    """Show expiry alert on startup if there are expiring items."""
    expiring = inventory.expiring_items()
    if expiring.get_length() > 0:
        expire_alert(expiring)
