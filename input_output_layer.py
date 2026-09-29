import ctypes
import os
from datetime import datetime
from rich import print
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.console import Console
from rich.text import Text

from logic_layer import inventory_count, validate_expiry_date
from data_layer import save_item_to_csv

DATE_FORMAT = "%d/%m/%Y"
console = Console()


# ==========================================
# PRESENTATION / DISPLAY FUNCTIONS
# ==========================================

def display_items(inventory, title):
    """Display inventory as a formatted table."""
    table = Table(title=title, show_header=True, header_style="bold purple")
    table.add_column("Food Name", no_wrap=True)
    table.add_column("Qty", style="cyan", justify="center")
    table.add_column("Expiry Date", style="cyan", justify="center")
    table.add_column("Days Left", style="cyan", justify="center")
    table.add_column("Status", justify="right")

    for item in inventory:
        raw_status = item["Status"]
        if "EXPIRED" in raw_status:
            status_formatted = "[bold red]EXPIRED[/bold red]"
        elif "EXPIRING" in raw_status:
            status_formatted = "[bold yellow]EXPIRING[/bold yellow]"
        elif "FRESH" in raw_status:
            status_formatted = "[bold green]FRESH[/bold green]"
        else:
            status_formatted = raw_status

        table.add_row(
            item["Food_Name"],
            str(item["Inventory_Quantity"]),
            item["Expiry_Date"],
            str(item["Days_Remaining"]),
            status_formatted
        )
    return table


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
    if len(expiring_inventory) > 0:
        expire_alert(expiring_inventory)


def do_nothing():
    print("User clicked No.")


def expire_alert(expiring_inventory):
    alert_title = 'Items are about to expire!'
    alert_text = f"{inventory_count(expiring_inventory)} items are about to expire! Would you like to view them?"

    if os.name == 'nt':
        result = ctypes.windll.user32.MessageBoxW(0, alert_text, alert_title, 4)
        if result == 6:
            print(display_items(expiring_inventory, "Expiring Items"))
        elif result == 7:
            do_nothing()
    else:
        choice = input(f"\n[Warning] {alert_text} (y/n): ").strip().lower()
        if choice == 'y':
            print(display_items(expiring_inventory, "Expiring Items"))
        else:
            do_nothing()


def add_food_item(inventory):
    """Stub function to allow adding items manually."""
    print("\n--- Add New Food Item ---")
    name = input("Enter food name: ").strip()
    qty = input("Enter quantity: ").strip()
    exp_date = input(f"Enter expiry date ({DATE_FORMAT}): ").strip()

    # Reject the item if the expiry date is invalid or more than MAX_YEARS away
    exp_dt, error = validate_expiry_date(exp_date)
    if error:
        print(f"[red]Error:[/red] {error}")
        return

    purch_date = datetime.now().strftime(DATE_FORMAT)

    try:
        days_rem = (exp_dt - datetime.now().date()).days
        if days_rem <= 0:
            status = "EXPIRED"
        elif days_rem <= 30:
            status = "EXPIRING"
        else:
            status = "FRESH"

        new_item = {
            "Food_Name": name,
            "Expiry_Date": exp_date,
            "Date_Purchased": purch_date,
            "Inventory_Quantity": int(qty),
            "Days_Remaining": days_rem,
            "Status": status
        }

        save_item_to_csv(new_item)   # write to CSV first
        inventory.append(new_item)   # then update the in-memory list
        print(f"[green]Success:[/green] Added '{name}' successfully!")

    except Exception as e:
        print(f"[red]Error:[/red] Failed to add item: {e}")
