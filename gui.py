#!/usr/bin/env python3
"""
Food Waste Management System - Tkinter GUI

Modern desktop GUI that integrates with the existing application layers:
- Data Layer: SQLite persistence via data_layer module
- Logic Layer: Validation via logic_layer module
- AI Layer: AI suggestions via ai_layer module (lazy-loaded)
- Item/Inventory classes from classes package

Run with: python gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

from data_layer import initialise_inventory, save_inventory, close_database, get_data_manager
from logic_layer import validate_expiry_date, validate_food_name, validate_qty
from classes.inventory import Inventory
from classes.item import Item

# AI Service (lazy-loaded to avoid API key requirement at startup)
_ai_service = None


def get_ai_service():
    """Return the shared AIService instance, creating it when necessary."""
    global _ai_service
    if _ai_service is None:
        from ai_layer import AIService
        from classes.ai_client import GeminiClient
        from classes.ai_prompt import KitchenPromptBuilder
        client = GeminiClient()
        _ai_service = AIService(client=client, prompt_builder=KitchenPromptBuilder())
    return _ai_service


def inventory_to_ai_format(inventory: Inventory) -> list:
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


class FoodWasteGUI(tk.Tk):
    """Modern Desktop GUI for the Food Waste Management System."""

    def __init__(self):
        super().__init__()
        self.title("Food Waste Management System")
        self.geometry("1100x700")
        self.minsize(900, 550)

        # Initialize Data Layer and State
        self.inventory = initialise_inventory()
        self.data_manager = get_data_manager()

        self._configure_styles()
        self._build_layout()
        self.refresh_table()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _configure_styles(self):
        """Configure clean UI styles using ttk."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e1e1e1")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="white", background="#2c3e50")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def _build_layout(self):
        """Build the main window layout with a split pane."""
        # Top Header Banner
        header = tk.Frame(self, bg="#2c3e50", padx=20, pady=15)
        header.pack(fill=tk.X)

        ttk.Label(
            header,
            text="🌱 Food Waste Management & Prevention System",
            style="Header.TLabel"
        ).pack(side=tk.LEFT)

        # Time label
        self.time_label = ttk.Label(header, text="", font=("Segoe UI", 10), foreground="#bdc3c7", background="#2c3e50")
        self.time_label.pack(side=tk.RIGHT)
        self._update_clock()

        # Main Split Paned Window
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- LEFT SIDE: Inventory Table & Action Buttons ---
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)

        # Action Buttons Toolbar
        btn_toolbar = ttk.Frame(left_frame)
        btn_toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btn_toolbar, text="➕ Add Item", command=self.open_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_toolbar, text="✏️ Update Item", command=self.open_update_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_toolbar, text="🗑️ Delete Item", command=self.delete_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_toolbar, text="🔍 Search", command=self.open_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_toolbar, text="🔄 Refresh", command=self.refresh_table).pack(side=tk.RIGHT, padx=2)

        # Stats Bar
        self.stats_label = ttk.Label(left_frame, text="", font=("Segoe UI", 9), foreground="#666")
        self.stats_label.pack(fill=tk.X, pady=(0, 4), anchor=tk.W)

        # Treeview Table
        columns = ("Serial", "Name", "Qty", "Expiry", "Days Left", "Status")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")

        col_widths = {"Serial": 75, "Name": 200, "Qty": 60, "Expiry": 100, "Days Left": 85, "Status": 95}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to update
        self.tree.bind("<Double-1>", lambda e: self.open_update_dialog())

        # --- RIGHT SIDE: AI Assistant Panel ---
        right_frame = ttk.LabelFrame(main_pane, text=" AI Assistant & Insights ", padding=10)
        main_pane.add(right_frame, weight=2)

        # AI Button
        self.ai_button = ttk.Button(
            right_frame,
            text="🤖 Generate AI Suggestions & Recipes",
            command=self.fetch_ai_insights,
            style="Accent.TButton"
        )
        self.ai_button.pack(fill=tk.X, pady=(0, 10))

        # Quick Stats in AI Panel
        self.ai_stats_frame = ttk.Frame(right_frame)
        self.ai_stats_frame.pack(fill=tk.X, pady=(0, 10))
        self._build_ai_stats()

        # AI Response Text Area with Scrollbar
        ai_container = ttk.Frame(right_frame)
        ai_container.pack(fill=tk.BOTH, expand=True)

        self.ai_output = tk.Text(ai_container, wrap=tk.WORD, font=("Consolas", 9), bg="#f8f9fa", padx=10, pady=10)
        ai_scroll = ttk.Scrollbar(ai_container, orient=tk.VERTICAL, command=self.ai_output.yview)
        self.ai_output.configure(yscroll=ai_scroll.set)

        self.ai_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ai_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure text tags for formatting
        self.ai_output.tag_configure("header", font=("Consolas", 10, "bold"), foreground="#2c3e50")
        self.ai_output.tag_configure("section", font=("Consolas", 10, "bold"), foreground="#2980b9")
        self.ai_output.tag_configure("content", font=("Consolas", 9), foreground="#34495e")
        self.ai_output.tag_configure("error", font=("Consolas", 9), foreground="#e74c3c")
        self.ai_output.tag_configure("success", font=("Consolas", 9), foreground="#27ae60")

    def _build_ai_stats(self):
        """Build quick stats display in AI panel."""
        self.ai_stat_labels = {}
        for label_text, color in [
            ("Total", "#2c3e50"),
            ("Expired", "#e74c3c"),
            ("Expiring", "#f39c12"),
            ("Fresh", "#27ae60")
        ]:
            frame = ttk.Frame(self.ai_stats_frame)
            frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            ttk.Label(frame, text=label_text, font=("Segoe UI", 8), foreground=color).pack()
            val_label = ttk.Label(frame, text="0", font=("Segoe UI", 12, "bold"), foreground=color)
            val_label.pack()
            self.ai_stat_labels[label_text.lower()] = val_label

    def _update_clock(self):
        """Update the clock in the header."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"🕐 {now}")
        self.after(1000, self._update_clock)

    def refresh_table(self):
        """Reloads inventory data from database and updates the GUI table."""
        self.inventory = initialise_inventory()

        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in self.inventory.get_items():
            status = item.status
            tag = "expired" if "EXPIRED" in status else ("expiring" if "EXPIRING" in status else "fresh")

            self.tree.insert("", tk.END, values=(
                item.serial_number,
                item.food_name,
                item.inventory_quantity,
                item.expiry_date,
                item.days_remaining,
                item.status
            ), tags=(tag,))

        # Row Highlighting Colors
        self.tree.tag_configure("expired", background="#f8d7da")    # Soft Red
        self.tree.tag_configure("expiring", background="#fff3cd")   # Soft Yellow
        self.tree.tag_configure("fresh", background="#d4edda")      # Soft Green

        # Update stats
        self._update_stats()

    def _update_stats(self):
        """Update stats labels."""
        items = self.inventory.get_items()
        total = len(items)
        expired = sum(1 for item in items if item.status == "EXPIRED")
        expiring = sum(1 for item in items if item.status == "EXPIRING")
        fresh = total - expired - expiring

        self.stats_label.config(text=f"Total: {total}  |  Expired: {expired}  |  Expiring: {expiring}  |  Fresh: {fresh}")

        if hasattr(self, 'ai_stat_labels'):
            self.ai_stat_labels["total"].config(text=str(total))
            self.ai_stat_labels["expired"].config(text=str(expired))
            self.ai_stat_labels["expiring"].config(text=str(expiring))
            self.ai_stat_labels["fresh"].config(text=str(fresh))

    def open_add_dialog(self):
        ItemDialog(self, title="Add New Food Item", inventory=self.inventory, data_manager=self.data_manager, callback=self.refresh_table)

    def open_update_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Warning", "Please select an item from the table to update.")
            return
        item_values = self.tree.item(selected[0], "values")
        ItemDialog(self, title="Update Food Item", inventory=self.inventory, data_manager=self.data_manager, callback=self.refresh_table, item_data=item_values)

    def open_search_dialog(self):
        SearchDialog(self, data_manager=self.data_manager)

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Warning", "Please select an item to delete.")
            return

        serial_number = self.tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete item #{serial_number}?"):
            # Delete from database
            self.data_manager.delete_item(serial_number, self.inventory)
            # Refresh from database
            self.refresh_table()
            messagebox.showinfo("Success", "Item successfully deleted.")

    def fetch_ai_insights(self):
        """Spawns a background thread to call AI without freezing the UI."""
        self.ai_button.config(state=tk.DISABLED)
        self.ai_output.delete("1.0", tk.END)
        self.ai_output.insert(tk.END, "Analyzing inventory with AI... Please wait...\n", "content")

        def worker():
            try:
                ai_service = get_ai_service()
                ai_inventory = inventory_to_ai_format(self.inventory)

                if not ai_inventory:
                    sections = {"error": "Inventory is empty. Add some items first!"}
                else:
                    response = ai_service.process_inventory(ai_inventory)

                    # Convert Pydantic response to dict format for display
                    sections = {
                        "recipes": "\n".join(f"• {recipe}" for recipe in response.recipe_suggestions) if response.recipe_suggestions else "No recipes available",
                        "waste_trends": response.waste_trend_summary,
                        "immediate_action": "\n".join(
                            f"• {item.food_name} ({item.days_remaining}d left): {item.recommended_action}"
                            for item in response.items if item.waste_risk_level.lower() == "high"
                        ) if response.items else "No immediate actions",
                        "resupply": response.resupply_recommendations,
                    }
            except Exception as e:
                sections = {"error": str(e)}

            # Safely schedule the UI update back on the main Tkinter thread
            self.after(0, lambda: self._display_ai_results(sections))

        # Start background thread (daemon=True ensures it closes when the app exits)
        threading.Thread(target=worker, daemon=True).start()

    def _display_ai_results(self, sections):
        """Updates the text widget on the main GUI thread."""
        self.ai_button.config(state=tk.NORMAL)
        self.ai_output.delete("1.0", tk.END)

        if not sections or "error" in sections:
            err = sections.get("error", "Unknown error") if sections else "No response"
            self.ai_output.insert(tk.END, f"❌ Error calling AI:\n{err}\n", "error")
            return

        # Format with nice headers
        sections_data = [
            ("=== RECIPES TO PRIORITIZE ===", sections.get('recipes', 'None')),
            ("=== WASTE TRENDS ===", sections.get('waste_trends', 'None')),
            ("=== IMMEDIATE ACTION REQUIRED ===", sections.get('immediate_action', 'None')),
            ("=== RESUPPLY RECOMMENDATIONS ===", sections.get('resupply', 'None')),
        ]

        for i, (header, content) in enumerate(sections_data):
            if i > 0:
                self.ai_output.insert(tk.END, "\n\n")
            self.ai_output.insert(tk.END, f"{header}\n", "section")
            self.ai_output.insert(tk.END, f"{content}\n", "content")

        self.ai_output.see(tk.END)

    def on_closing(self):
        """Handle window close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit? Changes will be saved."):
            save_inventory(self.inventory)
            close_database()
            self.destroy()


class ItemDialog(tk.Toplevel):
    """Popup modal window for adding or updating individual food items with validation."""

    def __init__(self, parent, title, inventory, data_manager, callback, item_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x320")
        self.resizable(False, False)
        self.transient(parent)  # Stay on top of parent
        self.grab_set()  # Modal

        self.inventory = inventory
        self.data_manager = data_manager
        self.callback = callback
        self.item_data = item_data

        self._build_widgets()
        self._center_window()

    def _center_window(self):
        """Center the dialog on parent window."""
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Food Name
        ttk.Label(main_frame, text="Food Name:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 2))
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))

        # Quantity
        ttk.Label(main_frame, text="Quantity:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 2))
        self.qty_entry = ttk.Entry(main_frame, width=40)
        self.qty_entry.pack(fill=tk.X, pady=(0, 10))

        # Expiry Date
        ttk.Label(main_frame, text="Expiry Date (DD/MM/YYYY):", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 2))
        self.exp_entry = ttk.Entry(main_frame, width=40)
        self.exp_entry.pack(fill=tk.X, pady=(0, 10))

        # Prefill if updating
        if self.item_data:
            # item_data format: (Serial_Number, Food_Name, Qty, Expiry_Date, Days_Remaining, Status)
            self.serial = self.item_data[0]
            self.name_entry.insert(0, self.item_data[1])
            self.qty_entry.insert(0, str(self.item_data[2]))
            self.exp_entry.insert(0, self.item_data[3])
        else:
            self.serial = None

        # Save Button
        ttk.Button(main_frame, text="Save Item", command=self.save_item, style="Accent.TButton").pack(pady=(10, 0))

        # Focus first field
        self.name_entry.focus_set()

    def save_item(self):
        name_input = self.name_entry.get()
        qty_input = self.qty_entry.get()
        exp_input = self.exp_entry.get()

        # Validate inputs using logic layer
        name, err = validate_food_name(name_input)
        if err:
            messagebox.showerror("Validation Error", err)
            return

        qty, err = validate_qty(qty_input)
        if err:
            messagebox.showerror("Validation Error", err)
            return

        exp_dt, err = validate_expiry_date(exp_input)
        if err:
            messagebox.showerror("Validation Error", err)
            return

        today = datetime.now().date()
        days_rem = (exp_dt - today).days
        if days_rem <= 0:
            status = "EXPIRED"
        elif days_rem <= 30:
            status = "EXPIRING"
        else:
            status = "FRESH"

        purch_date = datetime.now().strftime("%d/%m/%Y")

        if self.serial:
            # Update existing item
            item = self.inventory.search_item_by_serial(self.serial)
            if item:
                item.update(name, exp_input, purch_date, qty)
                self.data_manager.update_item(item, self.inventory)
                msg = "Item successfully updated."
            else:
                messagebox.showerror("Error", "Item not found in inventory.")
                return
        else:
            # Add new item - find next serial number
            existing = [int(item.serial_number) for item in self.inventory.get_items()]
            serial_num_str = str(max(existing, default=0) + 1).zfill(4)
            item = Item(serial_num_str, name, exp_input, purch_date, qty)
            self.inventory.add_item(item)
            self.data_manager.add_item(item, self.inventory)
            msg = "Item successfully added."

        save_inventory(self.inventory)
        self.callback()
        messagebox.showinfo("Success", msg)
        self.destroy()


class SearchDialog(tk.Toplevel):
    """Search dialog for finding items by keyword."""

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.title("Search Inventory")
        self.geometry("500x400")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.data_manager = data_manager
        self._build_widgets()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Search input
        ttk.Label(main_frame, text="Search Keyword (name or serial):", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))

        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        self.search_entry = ttk.Entry(search_frame, width=35)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())

        ttk.Button(search_frame, text="🔍 Search", command=self.perform_search).pack(side=tk.LEFT, padx=(5, 0))

        # Results
        columns = ("Serial", "Name", "Qty", "Expiry", "Days Left", "Status")
        self.results_tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="browse")

        col_widths = {"Serial": 70, "Name": 150, "Qty": 50, "Expiry": 90, "Days Left": 80, "Status": 80}
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=col_widths.get(col, 80), anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.search_entry.focus_set()

    def perform_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("Warning", "Please enter a search keyword.")
            return

        results = self.data_manager.search_items(keyword)

        for row in self.results_tree.get_children():
            self.results_tree.delete(row)

        if results:
            for item in results:
                tag = "expired" if "EXPIRED" in item.status else ("expiring" if "EXPIRING" in item.status else "fresh")
                self.results_tree.insert("", tk.END, values=(
                    item.serial_number,
                    item.food_name,
                    item.inventory_quantity,
                    item.expiry_date,
                    item.days_remaining,
                    item.status
                ), tags=(tag,))

            self.results_tree.tag_configure("expired", background="#f8d7da")
            self.results_tree.tag_configure("expiring", background="#fff3cd")
            self.results_tree.tag_configure("fresh", background="#d4edda")
        else:
            messagebox.showinfo("Search Results", f"No items found matching '{keyword}'.")


if __name__ == "__main__":
    app = FoodWasteGUI()
    app.mainloop()