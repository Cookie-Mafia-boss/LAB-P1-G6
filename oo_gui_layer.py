import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

from oo_data_layer import InventoryRepository
from oo_logic_layer import InventoryValidator, InventoryLogic
from oo_ai_layer import AIService

class FoodWasteGUI(tk.Tk):
    """Modern Desktop GUI for the Food Waste Management System."""

    def __init__(self):
        super().__init__()
        self.title("Food Waste Management System")
        self.geometry("1000x650")
        
        # Initialize Data Layer and State
        self.repository = InventoryRepository()
        self.inventory = self.repository.load_inventory()
        self._animate_loading = False

        self._configure_styles()
        self._build_layout()
        self.refresh_table()

    def _configure_styles(self):
        """Configure clean UI styles using ttk."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#e1e1e1")
        style.configure("Treeview", rowheight=26, font=("Arial", 10))

    def _build_layout(self):
        """Build the main window layout with a split pane."""
        # Top Header Banner
        header = tk.Frame(self, bg="#2c3e50", padx=15, pady=12)
        header.pack(fill=tk.X)
        tk.Label(
            header, 
            text="🌱 Food Waste Management & Prevention System", 
            font=("Arial", 16, "bold"), 
            fg="white", 
            bg="#2c3e50"
        ).pack(side=tk.LEFT)

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
        ttk.Button(btn_toolbar, text="🔄 Refresh", command=self.refresh_table).pack(side=tk.RIGHT, padx=2)

        # Treeview Table
        columns = ("Serial", "Name", "Qty", "Expiry", "Days Left", "Status")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        
        col_widths = {"Serial": 75, "Name": 180, "Qty": 60, "Expiry": 95, "Days Left": 80, "Status": 90}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- RIGHT SIDE: AI Assistant Panel ---
        right_frame = ttk.LabelFrame(main_pane, text=" AI Assistant & Insights ", padding=10)
        main_pane.add(right_frame, weight=2)

        self.ai_btn = ttk.Button(
            right_frame, 
            text="🤖 Generate AI Suggestions & Recipes", 
            command=self.fetch_ai_insights
        )
        self.ai_btn.pack(fill=tk.X, pady=(0, 8))

        # Progress Bar Frame (Hidden by default)
        self.progress_frame = ttk.Frame(right_frame)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        self.progress_label = ttk.Label(self.progress_frame, text="0%", font=("Arial", 9, "bold"), width=5)
        self.progress_label.pack(side=tk.RIGHT)

        # AI Response Text Area with Scrollbar
        ai_container = ttk.Frame(right_frame)
        ai_container.pack(fill=tk.BOTH, expand=True)

        self.ai_output = tk.Text(ai_container, wrap=tk.WORD, font=("Consolas", 9), bg="#f8f9fa", padx=8, pady=8)
        ai_scroll = ttk.Scrollbar(ai_container, orient=tk.VERTICAL, command=self.ai_output.yview)
        self.ai_output.configure(yscroll=ai_scroll.set)

        self.ai_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ai_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_table(self):
        """Reloads inventory data and updates the GUI table."""
        self.inventory = self.repository.load_inventory()
        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in self.inventory:
            status = item["Status"]
            tag = "expired" if "EXPIRED" in status else ("expiring" if "EXPIRING" in status else "fresh")
            
            self.tree.insert("", tk.END, values=(
                item["Serial_Number"],
                item["Food_Name"],
                item["Inventory_Quantity"],
                item["Expiry_Date"],
                item["Days_Remaining"],
                item["Status"]
            ), tags=(tag,))

        # Row Highlighting Colors
        self.tree.tag_configure("expired", background="#f8d7da")    # Soft Red
        self.tree.tag_configure("expiring", background="#fff3cd")   # Soft Yellow
        self.tree.tag_configure("fresh", background="#d4edda")      # Soft Green

    def open_add_dialog(self):
        ItemDialog(self, title="Add New Food Item", inventory=self.inventory, repository=self.repository, callback=self.refresh_table)

    def open_update_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Warning", "Please select an item from the table to update.")
            return
        item_values = self.tree.item(selected[0], "values")
        ItemDialog(self, title="Update Food Item", inventory=self.inventory, repository=self.repository, callback=self.refresh_table, item_data=item_values)

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Warning", "Please select an item to delete.")
            return
        
        serial_number = self.tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete item #{serial_number}?"):
            self.inventory = [item for item in self.inventory if item["Serial_Number"] != serial_number]
            for idx, item in enumerate(self.inventory, start=1):
                item["Serial_Number"] = f"{idx:04d}"
            
            self.repository.save_inventory(self.inventory)
            self.refresh_table()
            messagebox.showinfo("Success", "Item successfully deleted.")

    def fetch_ai_insights(self):
        """Spawns a true background thread with safe percentage tracking."""
        if self._animate_loading:
            return  # Prevent multiple overlapping calls

        self._animate_loading = True
        self.ai_btn.config(state=tk.DISABLED)
        self.ai_output.delete("1.0", tk.END)
        self.ai_output.insert(tk.END, "Connecting to Gemini AI and analyzing inventory...")

        # Show progress bar and reset to 0%
        self.progress_frame.pack(fill=tk.X, pady=(0, 8), before=self.ai_output.master)
        self.progress_var.set(0)
        self.progress_label.config(text="0%")

        # Start the smooth progress animation loop on the main thread
        self._run_progress_animation()

        def worker():
            """Runs network request safely in the background thread."""
            try:
                expiring = InventoryLogic.check_expiries(self.inventory)
                sections = AIService.get_ai_suggestions(self.inventory, expiring)
                result = {"sections": sections}
            except Exception as e:
                result = {"error": str(e)}

            # Safely hand results back to the main Tkinter thread
            self.after(0, lambda: self._on_ai_complete(result))

        # Start background daemon thread
        threading.Thread(target=worker, daemon=True).start()

    def _run_progress_animation(self):
        """ Smoothly increments percentage up to 90% while waiting for API response """
        if self._animate_loading:
            current_val = self.progress_var.get()
            if current_val < 90:
                current_val += 3
                self.progress_var.set(current_val)
                self.progress_label.config(text=f"{int(current_val)}%")
            self.after(100, self._run_progress_animation)

    def _on_ai_complete(self, result):
        """ Handles response arrival on the main thread """
        self._animate_loading = False
        self.progress_var.set(100)
        self.progress_label.config(text="100%")

        def cleanup():
            self.progress_frame.pack_forget()
            self.ai_btn.config(state=tk.NORMAL)
            self.ai_output.delete("1.0", tk.END)

            if "error" in result:
                self.ai_output.insert(tk.END, f"❌ Error calling Gemini API:\n{result['error']}")
                return

            sections = result["sections"]
            formatted_text = f"""=== RECIPES TO PRIORITIZE ===\n{sections.get('recipes', 'None')}\n
=== WASTE TRENDS ===\n{sections.get('waste_trends', 'None')}\n
=== IMMEDIATE ACTION REQUIRED ===\n{sections.get('immediate_action', 'None')}\n
=== RESUPPLY RECOMMENDATIONS ===\n{sections.get('resupply', 'None')}"""
            
            self.ai_output.insert(tk.END, formatted_text)

        # Brief pause at 100% so user sees completion, then render results
        self.after(300, cleanup)


class ItemDialog(tk.Toplevel):
    """Popup modal window for adding or updating individual food items with validation."""

    def __init__(self, parent, title, inventory, repository, callback, item_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("360x280")
        self.resizable(False, False)
        
        self.inventory = inventory
        self.repository = repository
        self.callback = callback
        self.item_data = item_data

        self._build_widgets()

    def _build_widgets(self):
        tk.Label(self, text="Food Name:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=25, pady=(15, 2))
        self.name_entry = ttk.Entry(self, width=35)
        self.name_entry.pack(padx=25, fill=tk.X)

        tk.Label(self, text="Quantity:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=25, pady=(10, 2))
        self.qty_entry = ttk.Entry(self, width=35)
        self.qty_entry.pack(padx=25, fill=tk.X)

        tk.Label(self, text="Expiry Date (DD/MM/YYYY):", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=25, pady=(10, 2))
        self.exp_entry = ttk.Entry(self, width=35)
        self.exp_entry.pack(padx=25, fill=tk.X)

        if self.item_data:
            self.serial = self.item_data[0]
            self.name_entry.insert(0, self.item_data[1])
            self.qty_entry.insert(0, self.item_data[2])
            self.exp_entry.insert(0, self.item_data[3])
        else:
            self.serial = None

        ttk.Button(self, text="Save Item", command=self.save_item).pack(pady=20)

    def save_item(self):
        name_input = self.name_entry.get()
        qty_input = self.qty_entry.get()
        exp_input = self.exp_entry.get()

        name, err = InventoryValidator.validate_food_name(name_input)
        if err:
            messagebox.showerror("Validation Error", err)
            return

        qty, err = InventoryValidator.validate_qty(qty_input)
        if err:
            messagebox.showerror("Validation Error", err)
            return

        exp_dt, err = InventoryValidator.validate_expiry_date(exp_input)
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
            for item in self.inventory:
                if item["Serial_Number"] == self.serial:
                    item["Food_Name"] = name
                    item["Inventory_Quantity"] = qty
                    item["Expiry_Date"] = exp_input
                    item["Date_Purchased"] = purch_date
                    item["Days_Remaining"] = days_rem
                    item["Status"] = status
                    break
            msg = "Item successfully updated."
        else:
            new_serial = f"{len(self.inventory) + 1:04d}"
            self.inventory.append({
                "Serial_Number": new_serial,
                "Food_Name": name,
                "Expiry_Date": exp_input,
                "Date_Purchased": purch_date,
                "Inventory_Quantity": qty,
                "Days_Remaining": days_rem,
                "Status": status
            })
            msg = "Item successfully added."

        self.repository.save_inventory(self.inventory)
        self.callback()
        messagebox.showinfo("Success", msg)
        self.destroy()


if __name__ == "__main__":
    app = FoodWasteGUI()
    app.mainloop()