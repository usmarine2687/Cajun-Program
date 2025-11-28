"""
Cajun Marine - Main Application (Phase 3A)
Unified GUI with PDF generation, validation, and backups.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import os
import sqlite3
from db import service
from db.init import initialize_database
import pdf_generator


class CajunMarineApp:
    """Main application window with unified navigation."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cajun Marine Management System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a3a52')
        
        # Ensure database exists
        # Run unified initializer (idempotent migrations + defaults)
        try:
            initialize_database()
        except Exception as e:
            print(f"Initializer warning: {e}")
        service.ensure_database_exists()
        
        # Auto-backup on startup
        success, message = service.auto_backup_on_startup()
        if not success:
            print(f"Warning: {message}")
        
        self.create_ui()
    
    # ============ Helper Methods ============
    
    def get_selected_id(self, tree, item_name="item"):
        """Get selected item ID from tree. Returns ID or None with error message."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", f"Please select a {item_name}")
            return None
        return tree.item(selection[0])['values'][0]
    
    def fetch_boat_by_id(self, boat_id):
        """Fetch boat details from database. Returns dict or None."""
        if not boat_id:
            return None
        try:
            conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM Boats WHERE boat_id = ?", (boat_id,))
            row = cur.fetchone()
            result = dict(row) if row else None
            conn.close()
            return result
        except Exception:
            return None
    
    def fetch_engine_by_id(self, engine_id):
        """Fetch engine details from database. Returns dict or None."""
        if not engine_id:
            return None
        try:
            conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM Engines WHERE engine_id = ?", (engine_id,))
            row = cur.fetchone()
            result = dict(row) if row else None
            conn.close()
            return result
        except Exception:
            return None
    
    def populate_boat_dropdown(self, customer_id, boat_combo, boat_var):
        """Populate boat dropdown for a customer."""
        if not customer_id:
            boat_combo['values'] = []
            boat_combo.set('')
            boat_combo['state'] = 'disabled'
            return
        
        boats = service.get_customer_boats(customer_id)
        if boats:
            boat_choices = [f"{b['boat_id']} - {b.get('year', 'N/A')} {b.get('make', '')} {b.get('model', '')}" for b in boats]
            boat_combo['values'] = boat_choices
            boat_combo['state'] = 'readonly'
        else:
            boat_combo['values'] = []
            boat_combo.set('')
            boat_combo['state'] = 'disabled'
    
    def populate_engine_dropdown(self, boat_id, engine_combo, engine_var):
        """Populate engine dropdown for a boat."""
        if not boat_id:
            engine_combo['values'] = []
            engine_combo.set('')
            engine_combo['state'] = 'disabled'
            return
        
        engines = service.get_boat_engines(boat_id)
        if engines:
            engine_choices = [f"{e['engine_id']} - {e.get('make', '')} {e.get('model', '')} ({e.get('hp', 'N/A')} HP)" for e in engines]
            engine_combo['values'] = engine_choices
            engine_combo['state'] = 'readonly'
        else:
            engine_combo['values'] = []
            engine_combo.set('')
            engine_combo['state'] = 'disabled'
        
    def create_ui(self):
        """Create main UI structure."""
        # Top navigation bar
        nav_frame = tk.Frame(self.root, bg='#0d1f2d', height=60)
        nav_frame.pack(side='top', fill='x')
        nav_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            nav_frame,
            text="Cajun Marine",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#0d1f2d'
        )
        title_label.pack(side='left', padx=20, pady=10)
        
        # Navigation buttons
        btn_style = {
            'font': ('Segoe UI', 11),
            'bg': '#2d6a9f',
            'fg': 'white',
            'activebackground': '#3d7aaf',
            'activeforeground': 'white',
            'relief': 'flat',
            'cursor': 'hand2',
            'padx': 20,
            'pady': 8
        }
        
        tk.Button(nav_frame, text="🏠 Dashboard", command=self.show_dashboard, **btn_style).pack(side='left', padx=5)
        tk.Button(nav_frame, text="Customers", command=self.show_customers, **btn_style).pack(side='left', padx=5)
        tk.Button(nav_frame, text="Tickets", command=self.show_tickets, **btn_style).pack(side='left', padx=5)
        tk.Button(nav_frame, text="Parts", command=self.show_parts, **btn_style).pack(side='left', padx=5)
        tk.Button(nav_frame, text="New Engines", command=self.show_new_engines, **btn_style).pack(side='left', padx=5)
        tk.Button(nav_frame, text="Estimates", command=self.show_estimates, **btn_style).pack(side='left', padx=5)
        
        # Settings and Backup buttons
        settings_style = btn_style.copy()
        settings_style['bg'] = '#6c757d'
        tk.Button(nav_frame, text="⚙️ Settings", command=self.show_settings, **settings_style).pack(side='right', padx=5)
        
        backup_style = btn_style.copy()
        backup_style['bg'] = '#5cb85c'
        tk.Button(nav_frame, text="💾 Backup", command=self.show_backup_menu, **backup_style).pack(side='right', padx=5)
        
        # Warning button for engine registration
        self.check_registration_warnings()
        
        # Main content area
        self.content_frame = tk.Frame(self.root, bg='white')
        self.content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        # Show dashboard by default
        self.show_dashboard()
        
    def check_registration_warnings(self):
        """Check for engines needing registration and show warning button if any."""
        engines = service.get_engines_needing_registration()
        if engines:
            warning_btn = tk.Button(
                self.root,
                text=f"⚠️ {len(engines)} Engine(s) Need Registration",
                font=('Segoe UI', 10, 'bold'),
                bg='#ff6b6b',
                fg='white',
                command=self.show_registration_warnings
            )
            warning_btn.place(relx=1.0, rely=0, anchor='ne', x=-10, y=10)
    
    def show_registration_warnings(self):
        """Show engines needing registration."""
        engines = service.get_engines_needing_registration()
        if not engines:
            messagebox.showinfo("Registration", "No engines need registration!")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Engines Needing Registration")
        win.geometry("800x400")
        
        tk.Label(
            win,
            text="⚠️ The following engines need Tohatsu registration:",
            font=('Segoe UI', 12, 'bold'),
            fg='#d9534f'
        ).pack(pady=10)
        
        tree = ttk.Treeview(win, columns=('HP', 'Model', 'Serial', 'Customer', 'Phone', 'Installed', 'Days'), show='headings')
        tree.heading('HP', text='HP')
        tree.heading('Model', text='Model')
        tree.heading('Serial', text='Serial #')
        tree.heading('Customer', text='Customer')
        tree.heading('Phone', text='Phone')
        tree.heading('Installed', text='Installed')
        tree.heading('Days', text='Days Overdue')
        
        tree.column('HP', width=60)
        tree.column('Model', width=120)
        tree.column('Serial', width=120)
        tree.column('Customer', width=150)
        tree.column('Phone', width=120)
        tree.column('Installed', width=100)
        tree.column('Days', width=100)
        
        for e in engines:
            install_date = datetime.strptime(e['date_installed'], '%Y-%m-%d')
            days_overdue = (datetime.now() - install_date).days - 30
            tree.insert('', 'end', values=(
                e['hp'],
                e['model'],
                e['serial_number'],
                e.get('customer_name', 'N/A'),
                e.get('customer_phone', 'N/A'),
                e['date_installed'],
                days_overdue
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Button(win, text="Close", command=win.destroy).pack(pady=10)
    
    def clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Show dashboard with key metrics."""
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="Dashboard",
            font=('Segoe UI', 24, 'bold'),
            bg='white'
        ).pack(pady=20)
        
        # Metrics frame
        metrics = tk.Frame(self.content_frame, bg='white')
        metrics.pack(pady=20)
        
        # Get some quick stats
        try:
            customers = service.list_customers()
            tickets = service.list_tickets()
            open_tickets = [t for t in tickets if t['status'] != 'Closed']
            engines = service.list_new_engines('In Stock')
            engines_needing_reg = service.get_engines_needing_registration()
            
            self.create_metric_card(metrics, "Total Customers", len(customers), 0, 0)
            self.create_metric_card(metrics, "Open Tickets", len(open_tickets), 0, 1)
            self.create_metric_card(metrics, "Engines In Stock", len(engines), 1, 0)
            self.create_metric_card(metrics, "Engines Need Registration", len(engines_needing_reg), 1, 1, 
                                  bg='#ff6b6b' if len(engines_needing_reg) > 0 else '#5cb85c')
        except Exception as e:
            tk.Label(metrics, text=f"Error loading metrics: {e}", fg='red').pack()
    
    def create_metric_card(self, parent, label, value, row, col, bg='#2d6a9f'):
        """Create a metric card."""
        card = tk.Frame(parent, bg=bg, width=200, height=120)
        card.grid(row=row, column=col, padx=15, pady=15)
        card.grid_propagate(False)
        
        tk.Label(
            card,
            text=str(value),
            font=('Segoe UI', 36, 'bold'),
            fg='white',
            bg=bg
        ).pack(expand=True)
        
        tk.Label(
            card,
            text=label,
            font=('Segoe UI', 12),
            fg='white',
            bg=bg
        ).pack()
    
    def show_customers(self):
        """Show customers list."""
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header,
            text="Customers",
            font=('Segoe UI', 20, 'bold'),
            bg='white'
        ).pack(side='left')
        
        tk.Button(
            header,
            text="Import from Excel",
            font=('Segoe UI', 11),
            bg='#f0ad4e',
            fg='white',
            command=lambda: self.import_customers_from_excel(tree)
        ).pack(side='right', padx=(5, 0))
        
        tk.Button(
            header,
            text="+ Add Customer",
            font=('Segoe UI', 11),
            bg='#5cb85c',
            fg='white',
            command=self.add_customer_dialog
        ).pack(side='right')
        
        # Search
        search_frame = tk.Frame(self.content_frame, bg='white')
        search_frame.pack(fill='x', pady=(0, 10))
        tk.Label(search_frame, text="Search:", bg='white').pack(side='left', padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side='left')
        search_var.trace('w', lambda *args: self.filter_customers(tree, search_var.get()))
        
        # Customers tree
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'Name', 'Phone', 'Email', 'Tax Exempt', 'Out of State'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)
        
        # Enable column sorting
        self.customer_sort_column = 'Name'
        self.customer_sort_reverse = False
        
        tree.heading('ID', text='ID', command=lambda: self.sort_customers(tree, 'ID'))
        tree.heading('Name', text='Name ▼', command=lambda: self.sort_customers(tree, 'Name'))
        tree.heading('Phone', text='Phone', command=lambda: self.sort_customers(tree, 'Phone'))
        tree.heading('Email', text='Email', command=lambda: self.sort_customers(tree, 'Email'))
        tree.heading('Tax Exempt', text='Tax Exempt', command=lambda: self.sort_customers(tree, 'Tax Exempt'))
        tree.heading('Out of State', text='Out of State', command=lambda: self.sort_customers(tree, 'Out of State'))
        
        tree.column('ID', width=50)
        tree.column('Name', width=200)
        tree.column('Phone', width=150)
        tree.column('Email', width=200)
        tree.column('Tax Exempt', width=100)
        tree.column('Out of State', width=100)
        
        tree.pack(fill='both', expand=True)
        
        # Load customers
        self.load_customers(tree)
        
        # Double-click to edit
        tree.bind('<Double-Button-1>', lambda e: self.edit_customer_dialog(tree))
    
    def load_customers(self, tree):
        """Load customers into tree."""
        tree.delete(*tree.get_children())
        customers = service.list_customers()
        
        # Sort customers based on current sort settings
        col_map = {'ID': 'customer_id', 'Name': 'name', 'Phone': 'phone', 'Email': 'email', 
                   'Tax Exempt': 'tax_exempt', 'Out of State': 'out_of_state'}
        sort_key = col_map.get(self.customer_sort_column, 'name')
        
        # Handle different data types for sorting
        if sort_key in ('customer_id', 'tax_exempt', 'out_of_state'):
            # Numeric fields
            customers.sort(key=lambda x: (x.get(sort_key) or 0), reverse=self.customer_sort_reverse)
        else:
            # String fields
            customers.sort(key=lambda x: (x.get(sort_key) or '').lower(), reverse=self.customer_sort_reverse)
        
        for c in customers:
            tree.insert('', 'end', values=(
                c['customer_id'],
                c['name'],
                c.get('phone') or '',
                c.get('email') or '',
                'Yes' if c.get('tax_exempt') else 'No',
                'Yes' if c.get('out_of_state') else 'No'
            ))
    
    def sort_customers(self, tree, column):
        """Sort customers by column."""
        # Toggle sort direction if same column, otherwise default to ascending
        if self.customer_sort_column == column:
            self.customer_sort_reverse = not self.customer_sort_reverse
        else:
            self.customer_sort_column = column
            self.customer_sort_reverse = False
        
        # Update column headings to show sort indicator
        for col in ('ID', 'Name', 'Phone', 'Email', 'Tax Exempt', 'Out of State'):
            if col == column:
                indicator = ' ▼' if not self.customer_sort_reverse else ' ▲'
                tree.heading(col, text=col + indicator)
            else:
                tree.heading(col, text=col)
        
        # Reload customers with new sort
        self.load_customers(tree)
    
    def filter_customers(self, tree, search_term):
        """Filter customers by search term."""
        tree.delete(*tree.get_children())
        customers = service.list_customers()
        search_lower = search_term.lower()
        for c in customers:
            if (search_lower in c['name'].lower() or 
                search_lower in (c.get('phone') or '').lower() or
                search_lower in (c.get('email') or '').lower()):
                tree.insert('', 'end', values=(
                    c['customer_id'],
                    c['name'],
                    c.get('phone') or '',
                    c.get('email') or '',
                    'Yes' if c.get('tax_exempt') else 'No',
                    'Yes' if c.get('out_of_state') else 'No'
                ))
    
    def import_customers_from_excel(self, tree):
        """Import customers from Excel file."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            created, updated, errors = service.import_customers_from_excel(file_path)
            
            # Show results
            message = f"Import completed:\n\n"
            message += f"✓ Created: {created} customers\n"
            message += f"✓ Updated: {updated} customers\n"
            
            if errors:
                message += f"\n⚠ Errors ({len(errors)}):\n"
                message += "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    message += f"\n... and {len(errors) - 5} more"
            
            if errors:
                messagebox.showwarning("Import Completed with Errors", message)
            else:
                messagebox.showinfo("Import Successful", message)
            
            # Refresh customer list
            self.show_customers()
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {str(e)}")
    
    def add_customer_dialog(self):
        """Show add customer dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Customer")
        dialog.geometry("400x400")
        
        tk.Label(dialog, text="Name:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Phone:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        phone_entry = tk.Entry(dialog, width=30)
        phone_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Email:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        email_entry = tk.Entry(dialog, width=30)
        email_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Address:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        address_text = tk.Text(dialog, width=30, height=3)
        address_text.grid(row=3, column=1, padx=5, pady=5)
        
        tax_exempt_var = tk.IntVar()
        tk.Checkbutton(dialog, text="Tax Exempt", variable=tax_exempt_var).grid(row=4, column=1, sticky='w', padx=5, pady=5)
        
        tk.Label(dialog, text="Certificate #:").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        cert_entry = tk.Entry(dialog, width=30)
        cert_entry.grid(row=5, column=1, padx=5, pady=5)
        
        out_of_state_var = tk.IntVar()
        tk.Checkbutton(dialog, text="Out of State", variable=out_of_state_var).grid(row=6, column=1, sticky='w', padx=5, pady=5)
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required")
                return
            
            # Validate phone
            phone = phone_entry.get().strip()
            if phone:
                valid, formatted_phone, error = service.validate_phone(phone)
                if not valid:
                    messagebox.showerror("Validation Error", error)
                    return
                phone = formatted_phone
            else:
                phone = None
            
            # Validate email
            email = email_entry.get().strip()
            if email:
                valid, error = service.validate_email(email)
                if not valid:
                    messagebox.showerror("Validation Error", error)
                    return
            else:
                email = None
            
            try:
                service.create_customer(
                    name,
                    phone or None,
                    email or None,
                    address_text.get('1.0', 'end').strip() or None,
                    tax_exempt_var.get(),
                    cert_entry.get().strip() or None,
                    out_of_state_var.get()
                )
                messagebox.showinfo("Success", "Customer added successfully")
                dialog.destroy()
                self.show_customers()  # Refresh
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add customer: {e}")
        
        tk.Button(dialog, text="Save", command=save, bg='#5cb85c', fg='white').grid(row=7, column=0, columnspan=2, pady=20)
    
    def edit_customer_dialog(self, tree):
        """Show edit customer dialog."""
        selection = tree.selection()
        if not selection:
            return
        
        customer_id = tree.item(selection[0])['values'][0]
        customer = service.get_customer(customer_id)
        if not customer:
            messagebox.showerror("Error", "Customer not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Customer")
        dialog.geometry("400x400")
        
        tk.Label(dialog, text="Name:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.insert(0, customer['name'])
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Phone:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        phone_entry = tk.Entry(dialog, width=30)
        phone_entry.insert(0, customer.get('phone') or '')
        phone_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Email:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        email_entry = tk.Entry(dialog, width=30)
        email_entry.insert(0, customer.get('email') or '')
        email_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Address:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        address_text = tk.Text(dialog, width=30, height=3)
        address_text.insert('1.0', customer.get('address') or '')
        address_text.grid(row=3, column=1, padx=5, pady=5)
        
        tax_exempt_var = tk.IntVar(value=customer.get('tax_exempt', 0))
        tk.Checkbutton(dialog, text="Tax Exempt", variable=tax_exempt_var).grid(row=4, column=1, sticky='w', padx=5, pady=5)
        
        tk.Label(dialog, text="Certificate #:").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        cert_entry = tk.Entry(dialog, width=30)
        cert_entry.insert(0, customer.get('tax_exempt_certificate') or '')
        cert_entry.grid(row=5, column=1, padx=5, pady=5)
        
        out_of_state_var = tk.IntVar(value=customer.get('out_of_state', 0))
        tk.Checkbutton(dialog, text="Out of State", variable=out_of_state_var).grid(row=6, column=1, sticky='w', padx=5, pady=5)
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required")
                return
            
            try:
                service.update_customer(
                    customer_id,
                    name=name,
                    phone=phone_entry.get().strip() or None,
                    email=email_entry.get().strip() or None,
                    address=address_text.get('1.0', 'end').strip() or None,
                    tax_exempt=tax_exempt_var.get(),
                    tax_exempt_certificate=cert_entry.get().strip() or None,
                    out_of_state=out_of_state_var.get()
                )
                messagebox.showinfo("Success", "Customer updated successfully")
                dialog.destroy()
                self.show_customers()  # Refresh
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update customer: {e}")
        
        tk.Button(dialog, text="Save", command=save, bg='#5cb85c', fg='white').grid(row=7, column=0, columnspan=2, pady=20)
    
    def show_tickets(self):
        """Show tickets list."""
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header,
            text="Tickets",
            font=('Segoe UI', 20, 'bold'),
            bg='white'
        ).pack(side='left')
        
        tk.Button(
            header,
            text="+ New Ticket",
            font=('Segoe UI', 11),
            bg='#5cb85c',
            fg='white',
            command=self.add_ticket_dialog
        ).pack(side='right')
        
        # Filter by status
        filter_frame = tk.Frame(self.content_frame, bg='white')
        filter_frame.pack(fill='x', pady=(0, 10))
        tk.Label(filter_frame, text="Filter:", bg='white').pack(side='left', padx=(0, 5))
        status_var = tk.StringVar(value="All")
        statuses = ['All', 'Open', 'Working', 'Awaiting Parts', 'Awaiting Customer', 
                   'Awaiting Payment', 'Awaiting Pickup', 'Closed']
        status_combo = ttk.Combobox(filter_frame, textvariable=status_var, values=statuses, state='readonly', width=20)
        status_combo.pack(side='left')
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.load_tickets(tree, status_var.get()))
        
        # Tickets tree
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'Customer', 'Boat', 'Engine', 'Description', 'Status', 'Opened', 'Total'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)
        
        tree.heading('ID', text='Ticket #')
        tree.heading('Customer', text='Customer')
        tree.heading('Boat', text='Boat')
        tree.heading('Engine', text='Engine')
        tree.heading('Description', text='Description')
        tree.heading('Status', text='Status')
        tree.heading('Opened', text='Date Opened')
        tree.heading('Total', text='Total')
        
        tree.column('ID', width=70)
        tree.column('Customer', width=180)
        tree.column('Boat', width=140)
        tree.column('Engine', width=280)
        tree.column('Description', width=220)
        tree.column('Status', width=120)
        tree.column('Opened', width=100)
        tree.column('Total', width=90)
        
        tree.pack(fill='both', expand=True)
        
        # Load tickets
        self.load_tickets(tree, "All")
        
        # Double-click to view details
        tree.bind('<Double-Button-1>', lambda e: self.view_ticket_details(tree))
        
        # Context menu
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="View Details", command=lambda: self.view_ticket_details(tree))
        menu.add_command(label="Add Part", command=lambda: self.add_ticket_part_dialog(tree))
        menu.add_command(label="Add Labor", command=lambda: self.add_ticket_labor_dialog(tree))
        menu.add_command(label="Add Deposit", command=lambda: self.add_deposit_dialog(tree))
        menu.add_command(label="Change Status", command=lambda: self.change_ticket_status_dialog(tree))
        
        def show_menu(e):
            if tree.selection():
                menu.post(e.x_root, e.y_root)
        tree.bind('<Button-3>', show_menu)

        # Inline status dropdown on click within Status column
        def on_tree_click(event):
            region = tree.identify("region", event.x, event.y)
            if region != "cell":
                return
            col = tree.identify_column(event.x)
            # Status column index (1-based): find actual index
            # Columns order: ID, Customer, Boat, Engine, Description, Status, Opened, Total
            if col != "#6":
                return
            item = tree.identify_row(event.y)
            if not item:
                return
            # Current status value
            values = tree.item(item, 'values')
            current_status = values[5]
            # Compute bbox for overlay
            bbox = tree.bbox(item, column=col)
            if not bbox:
                return
            x, y, width, height = bbox
            statuses = ['Open', 'Working', 'Awaiting Parts', 'Awaiting Customer',
                        'Awaiting Payment', 'Awaiting Pickup', 'Closed']
            status_var = tk.StringVar(value=current_status)
            combo = ttk.Combobox(tree, textvariable=status_var, values=statuses, state='readonly')
            combo.place(x=x + tree.winfo_rootx() - tree.winfo_rootx(),
                        y=y + tree.winfo_rooty() - tree.winfo_rooty(),
                        width=width, height=height)

            def commit_change(*args):
                new_status = status_var.get()
                # Persist via service
                ticket_id = int(values[0])
                try:
                    service.update_ticket_status(ticket_id, new_status)
                    # Update tree display
                    updated = list(values)
                    updated[5] = new_status
                    tree.item(item, values=tuple(updated))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update status: {e}")
                finally:
                    combo.destroy()

            combo.bind('<<ComboboxSelected>>', commit_change)
            combo.focus_set()

        tree.bind('<Button-1>', on_tree_click)
    
    def load_tickets(self, tree, status_filter):
        """Load tickets into tree."""
        tree.delete(*tree.get_children())
        
        if status_filter == "All":
            tickets = service.list_tickets()
        else:
            tickets = service.list_tickets(status_filter)

        # Ensure totals are accurate and gather engine summary
        for t in tickets:
            try:
                service.calculate_ticket_totals(t['ticket_id'])
            except Exception:
                pass
            # Fetch up-to-date details for description and engine
            try:
                details = service.get_ticket_details(t['ticket_id'])
            except Exception:
                details = t
            if details is None:
                details = {}
            engine_summary = 'N/A'
            if details.get('engine_id'):
                eng_type = details.get('engine_type') or details.get('engine') or ''
                eng_make = details.get('engine_make', '')
                eng_model = details.get('engine_model', '')
                eng_hp = details.get('engine_hp', '')
                eng_year = details.get('engine_year', '')
                eng_outdrive = details.get('engine_outdrive', '')
                # Format: Year Make Model HP Type (Outdrive if sterndrive)
                parts = [str(eng_year), eng_make, eng_model, f"{eng_hp}HP" if eng_hp else '', eng_type]
                if eng_type and 'sterndrive' in eng_type.lower() and eng_outdrive:
                    parts.append(f"({eng_outdrive})")
                engine_summary = ' '.join(p for p in parts if p).strip()
                engine_summary = ' '.join(engine_summary.split())  # normalize spaces

            tree.insert('', 'end', values=(
                t['ticket_id'],
                t.get('customer_name', 'N/A'),
                f"{t.get('boat_make', '')} {t.get('boat_model', '')}".strip() or 'N/A',
                engine_summary,
                ((details.get('description') or '') if isinstance(details.get('description', ''), str) else str(details.get('description', ''))).strip()[:120],
                t['status'],
                t['date_opened'],
                f"${(details.get('total', t.get('total', 0)) or 0):.2f}"
            ))
    
    def add_ticket_dialog(self):
        """Show add ticket dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Ticket")
        dialog.geometry("500x400")
        
        tk.Label(dialog, text="Customer:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        customers = service.list_customers()
        customer_choices = [f"{c['customer_id']} - {c['name']}" for c in customers]
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(dialog, textvariable=customer_var, values=customer_choices, width=40)
        customer_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Boat selection with quick-add
        tk.Label(dialog, text="Boat:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        boat_frame = tk.Frame(dialog)
        boat_frame.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        boat_var = tk.StringVar()
        boat_combo = ttk.Combobox(boat_frame, textvariable=boat_var, width=32)
        boat_combo.pack(side='left')
        
        tk.Button(
            boat_frame,
            text="+ Add Boat",
            font=('Segoe UI', 8),
            bg='#5cb85c',
            fg='white',
            command=lambda: self.quick_add_boat_dialog(customer_var, boat_combo)
        ).pack(side='left', padx=5)
        
        def update_boats(*args):
            if customer_var.get():
                customer_id = int(customer_var.get().split(' - ')[0])
                # Get boats for this customer
                boats = []
                try:
                    conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                    cur = conn.cursor()
                    cur.execute("SELECT boat_id, year, make, model FROM Boats WHERE customer_id = ?", (customer_id,))
                    boats = [f"{b[0]} - {b[1]} {b[2]} {b[3]}" for b in cur.fetchall()]
                    conn.close()
                except:
                    pass
                boat_combo['values'] = boats
                if boats:
                    boat_combo.current(0)
        
        customer_var.trace('w', update_boats)
        
        # Engine selection (optional) with quick-add
        tk.Label(dialog, text="Engine (Optional):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        engine_frame = tk.Frame(dialog)
        engine_frame.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        engine_var = tk.StringVar()
        engine_combo = ttk.Combobox(engine_frame, textvariable=engine_var, width=32)
        engine_combo.pack(side='left')
        
        tk.Button(
            engine_frame,
            text="+ Add Engine",
            font=('Segoe UI', 8),
            bg='#5cb85c',
            fg='white',
            command=lambda: self.quick_add_engine_dialog(boat_var, engine_combo)
        ).pack(side='left', padx=5)
        
        # Populate engines for selected boat
        def update_engines(*args):
            if boat_var.get():
                boat_id = int(boat_var.get().split(' - ')[0])
                engines = []
                try:
                    conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                    cur = conn.cursor()
                    cur.execute("SELECT engine_id, engine_type, make, model, hp FROM Engines WHERE boat_id = ?", (boat_id,))
                    engines = [f"{e[0]} - {e[2]} {e[3]} ({e[4]} HP {e[1] if e[1] else ''})" for e in cur.fetchall()]
                    conn.close()
                except:
                    pass
                engine_combo['values'] = engines
        
        boat_var.trace('w', update_engines)
        
        tk.Label(dialog, text="Description:").grid(row=3, column=0, sticky='ne', padx=5, pady=5)
        desc_text = tk.Text(dialog, width=40, height=8)
        desc_text.grid(row=3, column=1, padx=5, pady=5)
        
        def save():
            if not customer_var.get() or not boat_var.get():
                messagebox.showerror("Error", "Customer and Boat are required")
                return
            
            try:
                customer_id = int(customer_var.get().split(' - ')[0])
                boat_id = int(boat_var.get().split(' - ')[0])
                engine_id = int(engine_var.get().split(' - ')[0]) if engine_var.get() else None
                description = desc_text.get('1.0', 'end').strip() or None
                
                ticket_id = service.create_ticket(customer_id, boat_id, engine_id, description)
                messagebox.showinfo("Success", f"Ticket #{ticket_id} created successfully")
                dialog.destroy()
                self.show_tickets()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create ticket: {e}")
        
        tk.Button(dialog, text="Create Ticket", command=save, bg='#5cb85c', fg='white').grid(row=4, column=0, columnspan=2, pady=20)
    
    def view_ticket_details(self, tree):
        """Show ticket details dialog."""
        selection = tree.selection()
        if not selection:
            return
        
        ticket_id = tree.item(selection[0])['values'][0]
        # Always recalculate totals on open so summary is current
        try:
            service.calculate_ticket_totals(ticket_id)
        except Exception as e:
            print(f"Warning: could not recalc ticket {ticket_id} totals: {e}")
        ticket = service.get_ticket_details(ticket_id)
        if not ticket:
            messagebox.showerror("Error", "Ticket not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Ticket #{ticket_id} Details")
        dialog.geometry("800x650")
        
        # Header
        header = tk.Frame(dialog, bg='#2d6a9f')
        header.pack(fill='x')
        tk.Label(header, text=f"Ticket #{ticket_id}", font=('Segoe UI', 16, 'bold'), 
                fg='white', bg='#2d6a9f').pack(pady=10)
        
        # Tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Summary tab
        summary_frame = tk.Frame(notebook)
        notebook.add(summary_frame, text='Summary')
        
        info_text = tk.Text(summary_frame, wrap='word', height=20)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        summary = f"""Customer: {ticket.get('customer_name')} ({ticket.get('customer_phone', 'N/A')})
Boat: {ticket.get('boat_make', 'N/A')} {ticket.get('boat_model', 'N/A')}
Status: {ticket['status']}
Opened: {ticket['date_opened']}
Closed: {ticket.get('date_closed', 'N/A')}

Description:
{ticket.get('description', 'No description')}

    Customer Notes:
    {ticket.get('customer_notes', 'No customer notes')}

Financial Summary:
Subtotal: ${ticket.get('subtotal', 0):.2f}
Tax: ${ticket.get('tax_amount', 0):.2f}
Total: ${ticket.get('total', 0):.2f}
"""
        info_text.insert('1.0', summary)
        info_text.config(state='disabled')

        # Notes tab (editable)
        notes_frame = tk.Frame(notebook)
        notebook.add(notes_frame, text='Notes')
        tk.Label(notes_frame, text="Customer Notes (printed on invoice):").pack(anchor='w', padx=10, pady=(10, 0))
        notes_text = tk.Text(notes_frame, wrap='word', height=10)
        notes_text.pack(fill='both', expand=True, padx=10, pady=10)
        notes_text.insert('1.0', ticket.get('customer_notes', '') or '')
        
        def save_notes():
            content = notes_text.get('1.0', 'end').strip()
            try:
                service.set_ticket_notes(ticket_id, content)
                messagebox.showinfo("Success", "Notes saved")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save notes: {e}")
        
        tk.Button(notes_frame, text="Save Notes", command=save_notes, bg='#5cb85c', fg='white').pack(anchor='e', padx=10, pady=(0,10))
        
        # Parts tab
        parts_frame = tk.Frame(notebook)
        notebook.add(parts_frame, text='Parts')
        
        parts_tree = ttk.Treeview(parts_frame, columns=('Part', 'Quantity', 'Price', 'Total'), show='headings')
        parts_tree.heading('Part', text='Part Name')
        parts_tree.heading('Quantity', text='Quantity')
        parts_tree.heading('Price', text='Unit Price')
        parts_tree.heading('Total', text='Total')
        parts_tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        for part in ticket.get('parts', []):
            total = part['quantity_used'] * part['price']
            item_id = parts_tree.insert('', 'end', values=(
                part['part_name'],
                part['quantity_used'],
                f"${part['price']:.2f}",
                f"${total:.2f}"
            ))
            # Store ticket_part_id in item tags for deletion
            parts_tree.item(item_id, tags=(part['ticket_part_id'],))
        
        def delete_selected_part():
            selection = parts_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a part to delete")
                return
            
            if not messagebox.askyesno("Confirm Delete", "Delete this part from the ticket?"):
                return
            
            try:
                ticket_part_id = int(parts_tree.item(selection[0])['tags'][0])
                service.delete_ticket_part(ticket_part_id)
                service.calculate_ticket_totals(ticket_id)
                messagebox.showinfo("Success", "Part deleted")
                dialog.destroy()
                self.show_tickets()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete part: {e}")
        
        parts_btn_frame = tk.Frame(parts_frame)
        parts_btn_frame.pack(pady=5)
        tk.Button(parts_btn_frame, text="➕ Add Part", 
                 command=lambda: self.add_part_to_ticket(ticket_id, dialog),
                 bg='#5cb85c', fg='white').pack(side='left', padx=5)
        tk.Button(parts_btn_frame, text="🗑 Delete Selected", 
                 command=delete_selected_part,
                 bg='#d9534f', fg='white').pack(side='left', padx=5)
        
        # Labor tab
        labor_frame = tk.Frame(notebook)
        notebook.add(labor_frame, text='Labor')
        
        labor_tree = ttk.Treeview(labor_frame, columns=('Mechanic', 'Hours', 'Rate', 'Total', 'Description'), show='headings')
        labor_tree.heading('Mechanic', text='Mechanic')
        labor_tree.heading('Hours', text='Hours')
        labor_tree.heading('Rate', text='Rate')
        labor_tree.heading('Total', text='Total')
        labor_tree.heading('Description', text='Work Description')
        labor_tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        for labor in ticket.get('labor', []):
            total = labor['hours_worked'] * labor['labor_rate']
            item_id = labor_tree.insert('', 'end', values=(
                labor['mechanic_name'],
                labor['hours_worked'],
                f"${labor['labor_rate']:.2f}",
                f"${total:.2f}",
                labor.get('work_description', '')[:50]
            ))
            # Store assignment_id in item tags for deletion
            labor_tree.item(item_id, tags=(labor['assignment_id'],))
        
        def delete_selected_labor():
            selection = labor_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a labor entry to delete")
                return
            
            if not messagebox.askyesno("Confirm Delete", "Delete this labor entry from the ticket?"):
                return
            
            try:
                assignment_id = int(labor_tree.item(selection[0])['tags'][0])
                service.delete_ticket_labor(assignment_id)
                service.calculate_ticket_totals(ticket_id)
                messagebox.showinfo("Success", "Labor entry deleted")
                dialog.destroy()
                self.show_tickets()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete labor: {e}")
        
        labor_btn_frame = tk.Frame(labor_frame)
        labor_btn_frame.pack(pady=5)
        tk.Button(labor_btn_frame, text="➕ Add Labor", 
                 command=lambda: self.add_labor_to_ticket(ticket_id, dialog),
                 bg='#5cb85c', fg='white').pack(side='left', padx=5)
        tk.Button(labor_btn_frame, text="🗑 Delete Selected", 
                 command=delete_selected_labor,
                 bg='#d9534f', fg='white').pack(side='left', padx=5)
        
        # Deposits tab
        deposits_frame = tk.Frame(notebook)
        notebook.add(deposits_frame, text='Deposits')
        
        deposits = service.get_ticket_deposits(ticket_id)
        balance_due = service.calculate_balance_due(ticket_id)
        
        tk.Label(deposits_frame, text=f"Balance Due: ${balance_due:.2f}", 
                font=('Segoe UI', 14, 'bold'), fg='red' if balance_due > 0 else 'green').pack(pady=10)
        
        deposits_tree = ttk.Treeview(deposits_frame, columns=('Date', 'Amount', 'Method', 'Notes'), show='headings')
        deposits_tree.heading('Date', text='Date')
        deposits_tree.heading('Amount', text='Amount')
        deposits_tree.heading('Method', text='Method')
        deposits_tree.heading('Notes', text='Notes')
        deposits_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        for dep in deposits:
            deposits_tree.insert('', 'end', values=(
                dep['payment_date'],
                f"${dep['amount']:.2f}",
                dep.get('payment_method') or 'N/A',
                (dep.get('notes') or '')[:50]
            ))
        
        deposits_btn_frame = tk.Frame(deposits_frame)
        deposits_btn_frame.pack(pady=5)
        tk.Button(deposits_btn_frame, text="💵 Add Payment", 
                 command=lambda: self.add_deposit_to_ticket(ticket_id, dialog),
                 bg='#5cb85c', fg='white').pack(side='left', padx=5)
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="📄 Print PDF", command=lambda: self.print_ticket_pdf(ticket_id), 
                 bg='#5cb85c', fg='white', font=('Segoe UI', 10)).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Close", command=dialog.destroy, font=('Segoe UI', 10)).pack(side='left', padx=5)
    
    def add_ticket_part_dialog(self, tree):
        """Add part to selected ticket."""
        ticket_id = self.get_selected_id(tree, "ticket")
        if not ticket_id:
            return
        
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Part to Ticket")
        dialog.geometry("400x200")
        
        tk.Label(dialog, text="Part:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        parts = service.list_parts()
        part_choices = [
            f"{p['part_id']} - {p['name']}" +
            (f" (PN: {p['part_number']})" if p.get('part_number') else "") +
            f" (${p['price']:.2f})" for p in parts
        ]
        part_var = tk.StringVar()
        part_combo = ttk.Combobox(dialog, textvariable=part_var, values=part_choices, width=40)
        part_combo.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(dialog, text="Quick Add New", command=lambda: self.quick_add_part_to_ticket(part_var, part_combo),
                  bg='#2d6a9f', fg='white').grid(row=0, column=2, padx=5, pady=5)
        
        tk.Label(dialog, text="Quantity:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        qty_entry = tk.Entry(dialog, width=40)
        qty_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def save():
            if not part_var.get() or not qty_entry.get():
                messagebox.showerror("Error", "Part and Quantity are required")
                return
            
            try:
                part_id = int(part_var.get().split(' - ')[0])
                quantity = int(qty_entry.get().strip())
                
                service.add_ticket_part(ticket_id, part_id, quantity)
                # Recalculate financial totals
                try:
                    service.calculate_ticket_totals(ticket_id)
                except Exception as calc_err:
                    print(f"Warning: failed to recalc totals: {calc_err}")
                messagebox.showinfo("Success", "Part added to ticket")
                dialog.destroy()
                self.show_tickets()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add part: {e}")
        
        tk.Button(dialog, text="Add Part", command=save, bg='#5cb85c', fg='white').grid(row=2, column=0, columnspan=2, pady=20)
    
    def add_ticket_labor_dialog(self, tree):
        """Add labor to selected ticket."""
        ticket_id = self.get_selected_id(tree, "ticket")
        if not ticket_id:
            return
        
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Labor to Ticket")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Mechanic:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        # Get mechanics from database
        import sqlite3
        conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
        cur = conn.cursor()
        cur.execute("SELECT mechanic_id, name, hourly_rate FROM Mechanics ORDER BY name")
        mechanics = cur.fetchall()
        conn.close()
        
        mechanic_choices = [f"{m[0]} - {m[1]} (${m[2]:.2f}/hr)" for m in mechanics]
        mechanic_var = tk.StringVar()
        mechanic_combo = ttk.Combobox(dialog, textvariable=mechanic_var, values=mechanic_choices, width=40)
        mechanic_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Hours:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        hours_entry = tk.Entry(dialog, width=40)
        hours_entry.grid(row=1, column=1, padx=5, pady=5)

        # Computed customer rate display and optional override
        rate_var = tk.StringVar(value="")
        tk.Label(dialog, text="Customer Rate ($/hr):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        rate_display = tk.Label(dialog, textvariable=rate_var, anchor='w')
        rate_display.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        tk.Label(dialog, text="Override Rate ($/hr):").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        rate_override_entry = tk.Entry(dialog, width=40)
        rate_override_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Work Description:").grid(row=4, column=0, sticky='ne', padx=5, pady=5)
        desc_text = tk.Text(dialog, width=40, height=5)
        desc_text.grid(row=4, column=1, padx=5, pady=5)

        def refresh_rate(*args):
            try:
                # Determine engine class for ticket
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("SELECT engine_id FROM Tickets WHERE ticket_id = ?", (ticket_id,))
                tr = cur.fetchone()
                engine_class = None
                if tr and tr[0]:
                    cur.execute("SELECT engine_type FROM Engines WHERE engine_id = ?", (tr[0],))
                    er = cur.fetchone()
                    eng_type = (er[0].strip().lower() if er and er[0] else '').lower()
                    if 'outboard' in eng_type:
                        engine_class = 'outboard'
                    elif 'inboard' in eng_type:
                        engine_class = 'inboard'
                    elif 'stern' in eng_type or 'sterndrive' in eng_type:
                        engine_class = 'sterndrive'
                    elif 'pwc' in eng_type or 'jetski' in eng_type:
                        engine_class = 'pwc'
                # Load rates
                cur.execute("SELECT outboard, inboard, sterndrive, pwc FROM LaborRates WHERE id = 1")
                row = cur.fetchone()
                if not row:
                    # initialize defaults if missing
                    cur.execute("INSERT OR REPLACE INTO LaborRates (id, outboard, inboard, sterndrive, pwc) VALUES (1, 100.0, 120.0, 120.0, 120.0)")
                    conn.commit()
                    row = (100.0, 120.0, 120.0, 120.0)
                rates = {
                    'outboard': float(row[0]),
                    'inboard': float(row[1]),
                    'sterndrive': float(row[2]),
                    'pwc': float(row[3])
                }
                # Fallback to mechanic hourly rate if engine not set
                display_rate = None
                if engine_class and engine_class in rates:
                    display_rate = rates[engine_class]
                else:
                    cur.execute("SELECT hourly_rate FROM Mechanics WHERE mechanic_id = ?", (int(mechanic_var.get().split(' - ')[0]) if mechanic_var.get() else -1,))
                    mr = cur.fetchone()
                    if mr and mr[0] is not None:
                        display_rate = float(mr[0])
                    else:
                        display_rate = rates['outboard']
                rate_var.set(f"${display_rate:.2f}")
                conn.close()
            except Exception:
                rate_var.set("$0.00")

        # Refresh rate when mechanic selection changes
        mechanic_var.trace('w', lambda *args: refresh_rate())
        refresh_rate()
        
        def save():
            if not mechanic_var.get() or not hours_entry.get():
                messagebox.showerror("Error", "Mechanic and Hours are required")
                return
            
            try:
                mechanic_id = int(mechanic_var.get().split(' - ')[0])
                hours = float(hours_entry.get().strip())
                description = desc_text.get('1.0', 'end').strip() or None
                # Use override rate if provided
                rate_override = rate_override_entry.get().strip()
                labor_rate = float(rate_override) if rate_override else None
                service.add_ticket_labor(ticket_id, mechanic_id, hours, description, labor_rate)
                messagebox.showinfo("Success", "Labor added to ticket")
                dialog.destroy()
                self.show_tickets()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add labor: {e}")
        
        tk.Button(dialog, text="Add Labor", command=save, bg='#5cb85c', fg='white').grid(row=5, column=0, columnspan=2, pady=20)
    
    def add_deposit_dialog(self, tree):
        """Add deposit to selected ticket."""
        ticket_id = self.get_selected_id(tree, "ticket")
        if not ticket_id:
            return
        
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Deposit")
        dialog.geometry("400x250")
        
        tk.Label(dialog, text="Amount:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        amount_entry = tk.Entry(dialog, width=40)
        amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Payment Method:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        payment_var = tk.StringVar(value="Cash")
        payment_combo = ttk.Combobox(dialog, textvariable=payment_var, 
                                    values=['Cash', 'Credit Card', 'Check', 'Insurance'], 
                                    width=40)
        payment_combo.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Notes:").grid(row=2, column=0, sticky='ne', padx=5, pady=5)
        notes_text = tk.Text(dialog, width=40, height=4)
        notes_text.grid(row=2, column=1, padx=5, pady=5)
        
        def save():
            if not amount_entry.get():
                messagebox.showerror("Error", "Amount is required")
                return
            
            try:
                amount = float(amount_entry.get().strip())
                payment_method = payment_var.get() or None
                notes = notes_text.get('1.0', 'end').strip() or None
                
                service.add_deposit(ticket_id, amount, payment_method, notes)
                
                balance = service.calculate_balance_due(ticket_id)
                messagebox.showinfo("Success", f"Deposit added. Balance due: ${balance:.2f}")
                dialog.destroy()
                self.show_tickets()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add deposit: {e}")
        
        tk.Button(dialog, text="Add Deposit", command=save, bg='#5cb85c', fg='white').grid(row=3, column=0, columnspan=2, pady=20)
    
    def change_ticket_status_dialog(self, tree):
        """Change status of selected ticket."""
        ticket_id = self.get_selected_id(tree, "ticket")
        if not ticket_id:
            return
        
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Ticket Status")
        dialog.geometry("300x150")
        
        tk.Label(dialog, text="New Status:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        statuses = ['Open', 'Working', 'Awaiting Parts', 'Awaiting Customer', 
                   'Awaiting Payment', 'Awaiting Pickup', 'Closed']
        status_var = tk.StringVar()
        status_combo = ttk.Combobox(dialog, textvariable=status_var, values=statuses, width=25)
        status_combo.grid(row=0, column=1, padx=5, pady=5)
        
        def save():
            if not status_var.get():
                messagebox.showerror("Error", "Status is required")
                return
            
            try:
                service.update_ticket_status(ticket_id, status_var.get())
                messagebox.showinfo("Success", f"Ticket status updated to '{status_var.get()}'")
                dialog.destroy()
                self.show_tickets()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update status: {e}")
        
        tk.Button(dialog, text="Update Status", command=save, bg='#5cb85c', fg='white').grid(row=1, column=0, columnspan=2, pady=20)
    
    def add_deposit_to_ticket(self, ticket_id, parent_dialog):
        """Add deposit/payment to ticket from detail view."""
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Payment")
        dialog.geometry("450x280")
        
        # Get current balance
        balance_due = service.calculate_balance_due(ticket_id)
        
        tk.Label(dialog, text=f"Current Balance Due: ${balance_due:.2f}", 
                font=('Segoe UI', 11, 'bold'), 
                fg='red' if balance_due > 0 else 'green').grid(row=0, column=0, columnspan=2, pady=(10, 15))
        
        tk.Label(dialog, text="Amount:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        amount_entry = tk.Entry(dialog, width=35)
        amount_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Quick button to pay full balance
        tk.Button(dialog, text="Pay Full Balance", 
                 command=lambda: amount_entry.delete(0, 'end') or amount_entry.insert(0, f"{balance_due:.2f}"),
                 bg='#0275d8', fg='white', font=('Segoe UI', 8)).grid(row=1, column=1, sticky='e', padx=5)
        
        tk.Label(dialog, text="Payment Method:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        payment_var = tk.StringVar(value="Cash")
        payment_combo = ttk.Combobox(dialog, textvariable=payment_var, 
                                    values=['Cash', 'Credit Card', 'Debit Card', 'Check', 'Insurance', 'Other'], 
                                    width=32)
        payment_combo.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        tk.Label(dialog, text="Notes:").grid(row=3, column=0, sticky='ne', padx=5, pady=5)
        notes_text = tk.Text(dialog, width=35, height=4)
        notes_text.grid(row=3, column=1, padx=5, pady=5)
        
        def save():
            if not amount_entry.get():
                messagebox.showerror("Error", "Amount is required")
                return
            
            try:
                amount = float(amount_entry.get().strip())
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be greater than 0")
                    return
                
                payment_method = payment_var.get() or "Cash"
                notes = notes_text.get('1.0', 'end').strip() or None
                
                service.add_deposit(ticket_id, amount, payment_method, notes)
                
                new_balance = service.calculate_balance_due(ticket_id)
                messagebox.showinfo("Success", f"Payment recorded!\n\nNew Balance Due: ${new_balance:.2f}\n\nClose and reopen ticket details to see updated information.")
                dialog.destroy()
                # Don't destroy parent_dialog - let user continue viewing ticket
                self.show_tickets()
            except ValueError:
                messagebox.showerror("Error", "Invalid amount")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add payment: {e}")
        
        tk.Button(dialog, text="Record Payment", command=save, bg='#5cb85c', fg='white', font=('Segoe UI', 10)).grid(row=4, column=0, columnspan=2, pady=20)
    
    def show_parts(self):
        """Show parts inventory."""
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header,
            text="Parts Inventory",
            font=('Segoe UI', 20, 'bold'),
            bg='white'
        ).pack(side='left')
        
        tk.Button(
            header,
            text="+ Add Part",
            font=('Segoe UI', 11),
            bg='#5cb85c',
            fg='white',
            command=self.add_part_dialog
        ).pack(side='right')
        
        # Search
        search_frame = tk.Frame(self.content_frame, bg='white')
        search_frame.pack(fill='x', pady=(0, 10))
        tk.Label(search_frame, text="Search:", bg='white').pack(side='left', padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side='left')
        search_var.trace('w', lambda *args: self.filter_parts(tree, search_var.get()))
        
        # Parts tree
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'Part#', 'Name', 'Stock', 'Price', 'Supplier', 'Cost', 'Retail', 'Taxable'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)
        
        tree.heading('ID', text='ID')
        tree.heading('Part#', text='Part #')
        tree.heading('Name', text='Part Name')
        tree.heading('Stock', text='Stock')
        tree.heading('Price', text='Price')
        tree.heading('Supplier', text='Supplier')
        tree.heading('Cost', text='Cost')
        tree.heading('Retail', text='Retail')
        tree.heading('Taxable', text='Taxable')
        
        tree.column('ID', width=50)
        tree.column('Part#', width=120)
        tree.column('Name', width=200)
        tree.column('Stock', width=80)
        tree.column('Price', width=80)
        tree.column('Supplier', width=150)
        tree.column('Cost', width=80)
        tree.column('Retail', width=80)
        tree.column('Taxable', width=80)
        
        tree.pack(fill='both', expand=True)
        
        # Load parts
        self.load_parts(tree)
        
        # Double-click to edit
        tree.bind('<Double-Button-1>', lambda e: self.edit_part_dialog(tree))
    
    def load_parts(self, tree):
        """Load parts into tree."""
        tree.delete(*tree.get_children())
        parts = service.list_parts()
        for p in parts:
            tree.insert('', 'end', values=(
                p['part_id'],
                p.get('part_number', ''),
                p['name'],
                p['stock_quantity'],
                f"${p['price']:.2f}",
                p.get('supplier_name', ''),
                f"${p.get('cost_from_supplier', 0):.2f}" if p.get('cost_from_supplier') else '',
                f"${p.get('retail_price', 0):.2f}" if p.get('retail_price') else '',
                'Yes' if p.get('taxable') else 'No'
            ))
    
    def filter_parts(self, tree, search_term):
        """Filter parts by search term."""
        tree.delete(*tree.get_children())
        parts = service.list_parts()
        search_lower = search_term.lower()
        for p in parts:
            if (search_lower in p.get('part_number', '').lower() or
                search_lower in p['name'].lower() or 
                search_lower in p.get('supplier_name', '').lower()):
                tree.insert('', 'end', values=(
                    p['part_id'],
                    p.get('part_number', ''),
                    p['name'],
                    p['stock_quantity'],
                    f"${p['price']:.2f}",
                    p.get('supplier_name', ''),
                    f"${p.get('cost_from_supplier', 0):.2f}" if p.get('cost_from_supplier') else '',
                    f"${p.get('retail_price', 0):.2f}" if p.get('retail_price') else '',
                    'Yes' if p.get('taxable') else 'No'
                ))
    
    def add_part_dialog(self):
        """Show add part dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Part")
        dialog.geometry("450x500")
        
        tk.Label(dialog, text="Part Number:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        part_number_entry = tk.Entry(dialog, width=35)
        part_number_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Part Name:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        name_entry = tk.Entry(dialog, width=35)
        name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Stock Quantity:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        stock_entry = tk.Entry(dialog, width=35)
        stock_entry.insert(0, "0")
        stock_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Supplier:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        supplier_entry = tk.Entry(dialog, width=35)
        supplier_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Cost from Supplier:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        cost_entry = tk.Entry(dialog, width=35)
        cost_entry.insert(0, "0.00")
        cost_entry.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Retail Price (Customer):*").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        retail_entry = tk.Entry(dialog, width=35)
        retail_entry.insert(0, "0.00")
        retail_entry.grid(row=5, column=1, padx=5, pady=5)
        
        taxable_var = tk.IntVar(value=1)
        tk.Checkbutton(dialog, text="Taxable", variable=taxable_var).grid(row=6, column=1, sticky='w', padx=5, pady=5)
        
        def save():
            part_number = part_number_entry.get().strip() or None
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Part name is required")
                return
            
            try:
                stock = int(stock_entry.get().strip())
                retail = float(retail_entry.get().strip()) if retail_entry.get().strip() else 0.0
                supplier = supplier_entry.get().strip() or None
                cost = float(cost_entry.get().strip()) if cost_entry.get().strip() else 0.0
                
                # Use retail price as the main price field
                service.create_part(part_number, name, stock, retail, supplier, cost, retail, taxable_var.get())
                messagebox.showinfo("Success", "Part added successfully")
                dialog.destroy()
                self.show_parts()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add part: {e}")
        
        tk.Button(dialog, text="Save", command=save, bg='#5cb85c', fg='white').grid(row=7, column=0, columnspan=2, pady=20)
    
    def edit_part_dialog(self, tree):
        """Show edit part dialog."""
        selection = tree.selection()
        if not selection:
            return
        
        part_id = tree.item(selection[0])['values'][0]
        part = service.get_part(part_id)
        if not part:
            messagebox.showerror("Error", "Part not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Part")
        dialog.geometry("450x500")
    
        tk.Label(dialog, text="Part Number:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        part_number_entry = tk.Entry(dialog, width=35)
        if part.get('part_number'):
            part_number_entry.insert(0, part['part_number'])
        part_number_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Part Name:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        name_entry = tk.Entry(dialog, width=35)
        name_entry.insert(0, part['name'])
        name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Stock Quantity:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        stock_entry = tk.Entry(dialog, width=35)
        stock_entry.insert(0, str(part['stock_quantity']))
        stock_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Supplier:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        supplier_entry = tk.Entry(dialog, width=35)
        supplier_entry.insert(0, part.get('supplier_name', ''))
        supplier_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Cost from Supplier:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        cost_entry = tk.Entry(dialog, width=35)
        if part.get('cost_from_supplier'):
            cost_entry.insert(0, str(part['cost_from_supplier']))
        cost_entry.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Retail Price (Customer):*").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        retail_entry = tk.Entry(dialog, width=35)
        retail_entry.insert(0, str(part.get('retail_price') or part['price']))
        retail_entry.grid(row=5, column=1, padx=5, pady=5)
        
        taxable_var = tk.IntVar(value=part.get('taxable', 1))
        tk.Checkbutton(dialog, text="Taxable", variable=taxable_var).grid(row=6, column=1, sticky='w', padx=5, pady=5)
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Part name is required")
                return
            
            try:
                retail = float(retail_entry.get().strip()) if retail_entry.get().strip() else 0.0
                updates = {
                    'part_number': part_number_entry.get().strip() or None,
                    'name': name,
                    'stock_quantity': int(stock_entry.get().strip()),
                    'price': retail,  # Use retail price as main price
                    'retail_price': retail,
                    'taxable': taxable_var.get()
                }
                
                if supplier_entry.get().strip():
                    updates['supplier_name'] = supplier_entry.get().strip()
                if cost_entry.get().strip():
                    updates['cost_from_supplier'] = float(cost_entry.get().strip())
                
                service.update_part(part_id, **updates)
                messagebox.showinfo("Success", "Part updated successfully")
                dialog.destroy()
                self.show_parts()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update part: {e}")
        
        tk.Button(dialog, text="Save", command=save, bg='#5cb85c', fg='white').grid(row=7, column=0, columnspan=2, pady=20)
    
    def show_new_engines(self):
        """Show new engines inventory."""
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header,
            text="New Tohatsu Engines Inventory",
            font=('Segoe UI', 20, 'bold'),
            bg='white'
        ).pack(side='left')
        
        tk.Button(
            header,
            text="+ Add Engine",
            font=('Segoe UI', 11),
            bg='#5cb85c',
            fg='white',
            command=self.add_new_engine_dialog
        ).pack(side='right')
        
        # Filter
        filter_frame = tk.Frame(self.content_frame, bg='white')
        filter_frame.pack(fill='x', pady=(0, 10))
        tk.Label(filter_frame, text="Filter:", bg='white').pack(side='left', padx=(0, 5))
        status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=status_var, 
                                    values=['All', 'In Stock', 'Sold', 'Transferred'], 
                                    state='readonly', width=15)
        status_combo.pack(side='left')
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.load_new_engines(tree, status_var.get()))
        
        # Engines tree
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'HP', 'Model', 'Serial', 'Status', 'Customer', 'Installed', 'Registered'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)
        
        tree.heading('ID', text='ID')
        tree.heading('HP', text='HP')
        tree.heading('Model', text='Model')
        tree.heading('Serial', text='Serial #')
        tree.heading('Status', text='Status')
        tree.heading('Customer', text='Customer')
        tree.heading('Installed', text='Date Installed')
        tree.heading('Registered', text='Registered')
        
        tree.column('ID', width=50)
        tree.column('HP', width=60)
        tree.column('Model', width=150)
        tree.column('Serial', width=120)
        tree.column('Status', width=100)
        tree.column('Customer', width=200)
        tree.column('Installed', width=100)
        tree.column('Registered', width=100)
        
        tree.pack(fill='both', expand=True)
        
        # Load engines
        self.load_new_engines(tree, "All")
        
        # Double-click to view/edit
        tree.bind('<Double-Button-1>', lambda e: self.view_new_engine_dialog(tree))
        
        # Context menu
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="View Details", command=lambda: self.view_new_engine_dialog(tree))
        menu.add_command(label="Sell Engine", command=lambda: self.sell_engine_dialog(tree))
        menu.add_command(label="Mark as Registered", command=lambda: self.mark_engine_registered(tree))
        
        def show_menu(e):
            if tree.selection():
                menu.post(e.x_root, e.y_root)
        tree.bind('<Button-3>', show_menu)
    
    def load_new_engines(self, tree, status_filter):
        """Load new engines into tree."""
        tree.delete(*tree.get_children())
        
        if status_filter == "All":
            engines = service.list_new_engines()
        else:
            engines = service.list_new_engines(status_filter)
        
        for e in engines:
            # Get customer name if sold
            customer_name = ''
            if e.get('customer_id'):
                customer = service.get_customer(e['customer_id'])
                if customer:
                    customer_name = customer['name']
            
            tree.insert('', 'end', values=(
                e['new_engine_id'],
                e['hp'],
                e['model'],
                e['serial_number'],
                e['status'],
                customer_name,
                e.get('date_installed', ''),
                'Yes' if e.get('registered_with_tohatsu') else 'No'
            ), tags=('needs_reg',) if self.engine_needs_registration(e) else ())
        
        # Highlight engines needing registration
        tree.tag_configure('needs_reg', background='#ffcccc')
    
    def engine_needs_registration(self, engine):
        """Check if engine needs registration."""
        if (engine.get('status') == 'Sold' and 
            engine.get('paid_in_full') == 1 and 
            engine.get('date_installed') and
            engine.get('registered_with_tohatsu') == 0):
            
            install_date = datetime.strptime(engine['date_installed'], '%Y-%m-%d')
            days_since = (datetime.now() - install_date).days
            return days_since > 30
        return False
    
    def add_new_engine_dialog(self):
        """Show add new engine dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Tohatsu Engine")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="HP:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        hp_entry = tk.Entry(dialog, width=30)
        hp_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Model:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        model_entry = tk.Entry(dialog, width=30)
        model_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Serial Number:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        serial_entry = tk.Entry(dialog, width=30)
        serial_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Purchase Price:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        purchase_entry = tk.Entry(dialog, width=30)
        purchase_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Notes:").grid(row=4, column=0, sticky='ne', padx=5, pady=5)
        notes_text = tk.Text(dialog, width=30, height=4)
        notes_text.grid(row=4, column=1, padx=5, pady=5)
        
        def save():
            if not hp_entry.get() or not model_entry.get() or not serial_entry.get():
                messagebox.showerror("Error", "HP, Model, and Serial Number are required")
                return
            
            # Validate serial number
            serial = serial_entry.get().strip()
            valid, error = service.validate_serial_number(serial)
            if not valid:
                messagebox.showerror("Validation Error", error)
                return
            
            # Validate HP is integer
            valid, error = service.validate_integer(hp_entry.get(), "HP", min_value=1, max_value=500)
            if not valid:
                messagebox.showerror("Validation Error", error)
                return
            
            try:
                hp = int(hp_entry.get().strip())
                model = model_entry.get().strip()
                purchase = float(purchase_entry.get().strip()) if purchase_entry.get().strip() else None
                notes = notes_text.get('1.0', 'end').strip() or None
                
                engine_id = service.create_new_engine(hp, model, serial, purchase, notes)
                messagebox.showinfo("Success", f"Engine added to inventory with ID: {engine_id}")
                dialog.destroy()
                self.show_new_engines()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", f"Serial number '{serial}' already exists in inventory!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add engine: {e}")
        
        tk.Button(dialog, text="Add Engine", command=save, bg='#5cb85c', fg='white').grid(row=5, column=0, columnspan=2, pady=20)
    
    def view_new_engine_dialog(self, tree):
        """Show engine details."""
        selection = tree.selection()
        if not selection:
            return
        
        engine_id = tree.item(selection[0])['values'][0]
        engine = service.get_new_engine(engine_id)
        if not engine:
            messagebox.showerror("Error", "Engine not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Engine #{engine_id} Details")
        dialog.geometry("500x400")
        
        info_text = tk.Text(dialog, wrap='word')
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        purchase_price = engine.get('purchase_price') or 0
        sale_price = engine.get('sale_price') or 0
        
        details = f"""Engine ID: {engine['new_engine_id']}
HP: {engine['hp']}
Model: {engine['model']}
Serial Number: {engine['serial_number']}
Status: {engine['status']}

Purchase Price: ${purchase_price:.2f}
Sale Price: ${sale_price:.2f}

Date Sold: {engine.get('date_sold') or 'N/A'}
Date Installed: {engine.get('date_installed') or 'N/A'}
Paid in Full: {'Yes' if engine.get('paid_in_full') else 'No'}

Registered with Tohatsu: {'Yes' if engine.get('registered_with_tohatsu') else 'No'}
Registration Date: {engine.get('registration_date') or 'N/A'}

Notes:
{engine.get('notes') or 'No notes'}
"""
        
        if engine.get('customer_id'):
            customer = service.get_customer(engine['customer_id'])
            if customer:
                details += f"\n\nCustomer: {customer['name']}\nPhone: {customer.get('phone', 'N/A')}"
        
        if self.engine_needs_registration(engine):
            install_date = datetime.strptime(engine['date_installed'], '%Y-%m-%d')
            days_overdue = (datetime.now() - install_date).days - 30
            details = f"⚠️  WARNING: Engine needs Tohatsu registration! ({days_overdue} days overdue)\n\n" + details
        
        info_text.insert('1.0', details)
        info_text.config(state='disabled')
        
        tk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def sell_engine_dialog(self, tree):
        """Sell selected engine."""
        selection = tree.selection()
        if not selection:
            return
        
        engine_id = tree.item(selection[0])['values'][0]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Sell Engine")
        dialog.geometry("400x400")
        
        tk.Label(dialog, text="Customer:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        customers = service.list_customers()
        customer_choices = [f"{c['customer_id']} - {c['name']}" for c in customers]
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(dialog, textvariable=customer_var, values=customer_choices, width=35)
        customer_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Sale Price:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        price_entry = tk.Entry(dialog, width=35)
        price_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Date Sold:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        date_entry = tk.Entry(dialog, width=35)
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        date_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Date Installed:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        install_entry = tk.Entry(dialog, width=35)
        install_entry.grid(row=3, column=1, padx=5, pady=5)
        
        paid_var = tk.IntVar()
        tk.Checkbutton(dialog, text="Paid in Full", variable=paid_var).grid(row=4, column=1, sticky='w', padx=5, pady=5)
        
        def save():
            if not customer_var.get() or not price_entry.get():
                messagebox.showerror("Error", "Customer and Sale Price are required")
                return
            
            try:
                customer_id = int(customer_var.get().split(' - ')[0])
                sale_price = float(price_entry.get().strip())
                date_sold = date_entry.get().strip() or None
                date_installed = install_entry.get().strip() or None
                
                success = service.sell_new_engine(
                    engine_id, customer_id, None, sale_price,
                    date_sold, date_installed, paid_var.get()
                )
                
                if success:
                    messagebox.showinfo("Success", "Engine sold successfully")
                    dialog.destroy()
                    self.show_new_engines()
                else:
                    messagebox.showerror("Error", "Failed to sell engine (may not be in stock)")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to sell engine: {e}")
        
        tk.Button(dialog, text="Sell Engine", command=save, bg='#5cb85c', fg='white').grid(row=5, column=0, columnspan=2, pady=20)
    
    def mark_engine_registered(self, tree):
        """Mark selected engine as registered."""
        selection = tree.selection()
        if not selection:
            return
        
        engine_id = tree.item(selection[0])['values'][0]
        
        try:
            registration_date = datetime.now().strftime('%Y-%m-%d')
            success = service.update_new_engine(
                engine_id,
                registered_with_tohatsu=1,
                registration_date=registration_date
            )
            
            if success:
                messagebox.showinfo("Success", f"Engine marked as registered on {registration_date}")
                self.show_new_engines()
            else:
                messagebox.showerror("Error", "Failed to update engine")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark as registered: {e}")
    
    def show_estimates(self):
        """Show estimates."""
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header,
            text="Estimates",
            font=('Segoe UI', 20, 'bold'),
            bg='white'
        ).pack(side='left')
        
        tk.Button(
            header,
            text="+ New Estimate",
            font=('Segoe UI', 11),
            bg='#5cb85c',
            fg='white',
            command=self.add_estimate_dialog
        ).pack(side='right')
        
        tk.Button(
            header,
            text="🔄 Recalculate All",
            font=('Segoe UI', 10),
            bg='#f0ad4e',
            fg='white',
            command=lambda: self.recalculate_all_estimates(tree)
        ).pack(side='right', padx=(0, 5))
        
        # Search
        search_frame = tk.Frame(self.content_frame, bg='white')
        search_frame.pack(fill='x', pady=(0, 10))
        tk.Label(search_frame, text="Search:", bg='white').pack(side='left', padx=(0, 5))
        search_entry = tk.Entry(search_frame, width=40)
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', lambda e: self.filter_estimates(tree, search_entry.get()))
        
        # Estimates tree
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'Date', 'Customer', 'Insurance', 'Subtotal', 'Tax', 'Total'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)
        
        tree.heading('ID', text='ID')
        tree.heading('Date', text='Date')
        tree.heading('Customer', text='Customer')
        tree.heading('Insurance', text='Insurance Info')
        tree.heading('Subtotal', text='Subtotal')
        tree.heading('Tax', text='Tax')
        tree.heading('Total', text='Total')
        
        tree.column('ID', width=50)
        tree.column('Date', width=100)
        tree.column('Customer', width=200)
        tree.column('Insurance', width=200)
        tree.column('Subtotal', width=100)
        tree.column('Tax', width=100)
        tree.column('Total', width=100)
        
        tree.pack(fill='both', expand=True)
        
        # Load estimates
        self.load_estimates(tree)
        
        # Double-click to view
        tree.bind('<Double-Button-1>', lambda e: self.view_estimate_dialog(tree))
        
        # Context menu
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="View Details", command=lambda: self.view_estimate_dialog(tree))
        menu.add_command(label="Add Line Item", command=lambda: self.add_estimate_line_item_dialog(tree))
        
        def show_menu(e):
            if tree.selection():
                menu.post(e.x_root, e.y_root)
        tree.bind('<Button-3>', show_menu)
    
    def recalculate_all_estimates(self, tree):
        """Recalculate totals for all estimates."""
        estimates = service.list_estimates()
        count = 0
        for est in estimates:
            service.calculate_estimate_totals(est['estimate_id'])
            count += 1
        
        # Reload the tree
        self.load_estimates(tree)
        messagebox.showinfo("Success", f"Recalculated totals for {count} estimate(s)")
    
    def load_estimates(self, tree):
        """Load estimates into tree."""
        tree.delete(*tree.get_children())
        estimates = service.list_estimates()
        
        for est in estimates:
            customer = service.get_customer(est['customer_id'])
            customer_name = customer['name'] if customer else 'Unknown'
            
            tree.insert('', 'end', values=(
                est['estimate_id'],
                est['estimate_date'],
                customer_name,
                est.get('insurance_info', ''),
                f"${est.get('subtotal', 0):.2f}",
                f"${est.get('tax_amount', 0):.2f}",
                f"${est.get('total', 0):.2f}"
            ))
    
    def filter_estimates(self, tree, search_term):
        """Filter estimates by search term."""
        tree.delete(*tree.get_children())
        estimates = service.list_estimates()
        
        for est in estimates:
            customer = service.get_customer(est['customer_id'])
            customer_name = customer['name'] if customer else 'Unknown'
            insurance_info = est.get('insurance_info', '')
            
            if (search_term.lower() in customer_name.lower() or 
                search_term.lower() in insurance_info.lower() or
                search_term in str(est['estimate_id'])):
                
                tree.insert('', 'end', values=(
                    est['estimate_id'],
                    est['estimate_date'],
                    customer_name,
                    insurance_info,
                    f"${est.get('subtotal', 0):.2f}",
                    f"${est.get('tax_amount', 0):.2f}",
                    f"${est.get('total', 0):.2f}"
                ))
    
    def add_estimate_dialog(self):
        """Create new estimate."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Estimate")
        dialog.geometry("450x550")
        
        tk.Label(dialog, text="Customer:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        customers = service.list_customers()
        customer_choices = [f"{c['customer_id']} - {c['name']}" for c in customers]
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(dialog, textvariable=customer_var, values=customer_choices, width=35)
        customer_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Boat:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        boat_var = tk.StringVar()
        boat_combo = ttk.Combobox(dialog, textvariable=boat_var, values=[], width=35, state='disabled')
        boat_combo.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Engine:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        engine_var = tk.StringVar()
        engine_combo = ttk.Combobox(dialog, textvariable=engine_var, values=[], width=35, state='disabled')
        engine_combo.grid(row=2, column=1, padx=5, pady=5)
        
        def on_customer_change(event):
            if not customer_var.get():
                self.populate_boat_dropdown(None, boat_combo, boat_var)
                self.populate_engine_dropdown(None, engine_combo, engine_var)
                return
            
            try:
                customer_id = int(customer_var.get().split(' - ')[0])
                self.populate_boat_dropdown(customer_id, boat_combo, boat_var)
                self.populate_engine_dropdown(None, engine_combo, engine_var)
            except Exception:
                pass
        
        def on_boat_change(event):
            if not boat_var.get():
                self.populate_engine_dropdown(None, engine_combo, engine_var)
                return
            
            try:
                boat_id = int(boat_var.get().split(' - ')[0])
                self.populate_engine_dropdown(boat_id, engine_combo, engine_var)
            except Exception:
                pass
        
        customer_combo.bind('<<ComboboxSelected>>', on_customer_change)
        boat_combo.bind('<<ComboboxSelected>>', on_boat_change)
        
        tk.Label(dialog, text="Insurance Company:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        insurance_entry = tk.Entry(dialog, width=35)
        insurance_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Claim Number:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        claim_entry = tk.Entry(dialog, width=35)
        claim_entry.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Notes:").grid(row=5, column=0, sticky='ne', padx=5, pady=5)
        notes_text = tk.Text(dialog, width=35, height=8)
        notes_text.grid(row=5, column=1, padx=5, pady=5)
        
        def save():
            if not customer_var.get():
                messagebox.showerror("Error", "Customer is required")
                return
            
            try:
                customer_id = int(customer_var.get().split(' - ')[0])
                
                boat_id = None
                if boat_var.get():
                    boat_id = int(boat_var.get().split(' - ')[0])
                
                engine_id = None
                if engine_var.get():
                    engine_id = int(engine_var.get().split(' - ')[0])
                
                insurance_company = insurance_entry.get().strip() or None
                claim_number = claim_entry.get().strip() or None
                notes = notes_text.get('1.0', 'end').strip() or None
                
                estimate_id = service.create_estimate(customer_id, boat_id, engine_id, insurance_company, claim_number, notes)
                messagebox.showinfo("Success", f"Estimate #{estimate_id} created. Add line items to complete.")
                dialog.destroy()
                self.show_estimates()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create estimate: {e}")
        
        tk.Button(dialog, text="Create Estimate", command=save, bg='#5cb85c', fg='white').grid(row=6, column=0, columnspan=2, pady=20)
    
    def view_estimate_dialog(self, tree):
        """View estimate details."""
        estimate_id = self.get_selected_id(tree, "estimate")
        if not estimate_id:
            return
        
        
        # Recalculate totals to ensure they're current
        service.calculate_estimate_totals(estimate_id)
        
        details = service.get_estimate_details(estimate_id)
        if not details:
            messagebox.showerror("Error", "Estimate not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Estimate #{estimate_id}")
        dialog.geometry("700x500")
        
        # Header info
        header = tk.Frame(dialog)
        header.pack(fill='x', padx=10, pady=10)
        
        customer = service.get_customer(details['customer_id'])
        customer_name = customer['name'] if customer else 'Unknown'
        
        tk.Label(header, text=f"Date: {details['estimate_date']}", font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        tk.Label(header, text=f"Customer: {customer_name}", font=('Segoe UI', 11)).pack(anchor='w')
        if details.get('insurance_info'):
            tk.Label(header, text=f"Insurance: {details['insurance_info']}", font=('Segoe UI', 11)).pack(anchor='w')
        
        # Line items
        tk.Label(dialog, text="Line Items:", font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
        
        line_frame = tk.Frame(dialog)
        line_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        line_tree = ttk.Treeview(
            line_frame,
            columns=('Description', 'Quantity', 'Price', 'Total'),
            show='headings',
            height=8
        )
        
        line_tree.heading('Description', text='Description')
        line_tree.heading('Quantity', text='Qty')
        line_tree.heading('Price', text='Unit Price')
        line_tree.heading('Total', text='Total')
        
        line_tree.column('Description', width=350)
        line_tree.column('Quantity', width=80)
        line_tree.column('Price', width=100)
        line_tree.column('Total', width=100)
        
        line_tree.pack(fill='both', expand=True)
        
        for item in details.get('line_items', []):
            line_tree.insert('', 'end', values=(
                item['description'],
                item['quantity'],
                f"${item['unit_price']:.2f}",
                f"${item['line_total']:.2f}"
            ))
        
        # Totals
        totals = tk.Frame(dialog)
        totals.pack(fill='x', padx=10, pady=10)
        
        tk.Label(totals, text=f"Subtotal: ${details.get('subtotal', 0):.2f}", font=('Segoe UI', 11)).pack(anchor='e')
        tk.Label(totals, text=f"Tax: ${details.get('tax_amount', 0):.2f}", font=('Segoe UI', 11)).pack(anchor='e')
        tk.Label(totals, text=f"Total: ${details.get('total', 0):.2f}", font=('Segoe UI', 14, 'bold')).pack(anchor='e')
        
        # Notes
        if details.get('notes'):
            tk.Label(dialog, text="Notes:", font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
            notes_label = tk.Label(dialog, text=details['notes'], wraplength=650, justify='left')
            notes_label.pack(anchor='w', padx=10, pady=(0, 10))
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Add Line Item", command=lambda: [dialog.destroy(), self.add_estimate_line_item_dialog_with_id(estimate_id)]).pack(side='left', padx=5)
        tk.Button(btn_frame, text="📄 Print PDF", command=lambda: self.print_estimate_pdf(estimate_id), 
                 bg='#5cb85c', fg='white', font=('Segoe UI', 10)).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side='left', padx=5)
    
    def add_estimate_line_item_dialog(self, tree):
        """Add line item to selected estimate."""
        estimate_id = self.get_selected_id(tree, "estimate")
        if not estimate_id:
            return
        
        self.add_estimate_line_item_dialog_with_id(estimate_id)
    
    def add_estimate_line_item_dialog_with_id(self, estimate_id):
        """Add line item with given estimate ID."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add Line Item to Estimate #{estimate_id}")
        dialog.geometry("400x250")
        
        tk.Label(dialog, text="Description:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        desc_entry = tk.Entry(dialog, width=35)
        desc_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Quantity:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        qty_entry = tk.Entry(dialog, width=35)
        qty_entry.insert(0, "1")
        qty_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Unit Price:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        price_entry = tk.Entry(dialog, width=35)
        price_entry.grid(row=2, column=1, padx=5, pady=5)
        
        taxable_var = tk.IntVar(value=1)
        tk.Checkbutton(dialog, text="Taxable", variable=taxable_var).grid(row=3, column=1, sticky='w', padx=5, pady=5)
        
        def save():
            if not desc_entry.get() or not qty_entry.get() or not price_entry.get():
                messagebox.showerror("Error", "All fields are required")
                return
            
            try:
                description = desc_entry.get().strip()
                quantity = float(qty_entry.get().strip())
                unit_price = float(price_entry.get().strip())
                
                # Use 'part' as default item_type (could make this selectable)
                service.add_estimate_line_item(estimate_id, 'part', description, quantity, unit_price)
                # Recalculate totals
                service.calculate_estimate_totals(estimate_id)
                messagebox.showinfo("Success", "Line item added")
                dialog.destroy()
                self.show_estimates()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add line item: {e}")
        
        tk.Button(dialog, text="Add Line Item", command=save, bg='#5cb85c', fg='white').grid(row=4, column=0, columnspan=2, pady=20)
    
    # ========== BOATS & ENGINES QUICK-ADD ==========
    
    def quick_add_boat_dialog(self, customer_var, boat_combo):
        """Quick-add boat dialog for ticket creation."""
        if not customer_var.get():
            messagebox.showerror("Error", "Please select a customer first")
            return
        
        customer_id = int(customer_var.get().split(' - ')[0])
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Boat")
        dialog.geometry("400x400")
        
        tk.Label(dialog, text="Year:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        year_entry = tk.Entry(dialog, width=30)
        year_entry.insert(0, str(datetime.now().year))
        year_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Make:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        make_entry = tk.Entry(dialog, width=30)
        make_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Model:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        model_entry = tk.Entry(dialog, width=30)
        model_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="VIN:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        vin_entry = tk.Entry(dialog, width=30)
        vin_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Color 1:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        color1_entry = tk.Entry(dialog, width=30)
        color1_entry.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Color 2:").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        color2_entry = tk.Entry(dialog, width=30)
        color2_entry.grid(row=5, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Color 3:").grid(row=6, column=0, sticky='e', padx=5, pady=5)
        color3_entry = tk.Entry(dialog, width=30)
        color3_entry.grid(row=6, column=1, padx=5, pady=5)
        
        def save():
            year = year_entry.get().strip()
            make = make_entry.get().strip()
            model = model_entry.get().strip()
            
            if not year or not make or not model:
                messagebox.showerror("Error", "Year, Make, and Model are required")
                return
            
            # Validate year
            valid, error = service.validate_integer(year, "Year", min_value=1900, max_value=2100)
            if not valid:
                messagebox.showerror("Validation Error", error)
                return
            
            try:
                # Insert boat into database
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO Boats (customer_id, year, make, model, vin, color1, color2, color3)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (customer_id, int(year), make, model, vin_entry.get().strip() or None,
                      color1_entry.get().strip() or None, color2_entry.get().strip() or None,
                      color3_entry.get().strip() or None))
                conn.commit()
                boat_id = cur.lastrowid
                conn.close()
                
                # Refresh boat dropdown
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("SELECT boat_id, year, make, model FROM Boats WHERE customer_id = ?", (customer_id,))
                boats = [f"{b[0]} - {b[1]} {b[2]} {b[3]}" for b in cur.fetchall()]
                conn.close()
                
                boat_combo['values'] = boats
                # Select the newly added boat
                new_boat_text = f"{boat_id} - {year} {make} {model}"
                boat_combo.set(new_boat_text)
                
                messagebox.showinfo("Success", f"Boat added successfully!")
                dialog.destroy()
            except sqlite3.IntegrityError as e:
                if 'vin' in str(e).lower() or 'UNIQUE' in str(e):
                    # VIN already exists - offer to transfer ownership
                    vin = vin_entry.get().strip()
                    
                    # Get existing boat info
                    conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT b.boat_id, b.year, b.make, b.model, b.customer_id, c.name
                        FROM Boats b
                        JOIN Customers c ON b.customer_id = c.customer_id
                        WHERE b.vin = ?
                    """, (vin,))
                    existing = cur.fetchone()
                    conn.close()
                    
                    if existing:
                        boat_id, boat_year, boat_make, boat_model, old_customer_id, old_customer_name = existing
                        
                        transfer = messagebox.askyesno(
                            "Boat Already Exists",
                            f"A boat with VIN '{vin}' already exists:\n\n"
                            f"{boat_year} {boat_make} {boat_model}\n"
                            f"Current Owner: {old_customer_name}\n\n"
                            f"Would you like to transfer ownership to the new customer?",
                            icon='question'
                        )
                        
                        if transfer:
                            try:
                                # Transfer ownership
                                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                                cur = conn.cursor()
                                cur.execute("""
                                    UPDATE Boats SET customer_id = ? WHERE boat_id = ?
                                """, (customer_id, boat_id))
                                conn.commit()
                                conn.close()
                                
                                # Refresh boat dropdown
                                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                                cur = conn.cursor()
                                cur.execute("SELECT boat_id, year, make, model FROM Boats WHERE customer_id = ?", (customer_id,))
                                boats = [f"{b[0]} - {b[1]} {b[2]} {b[3]}" for b in cur.fetchall()]
                                conn.close()
                                
                                boat_combo['values'] = boats
                                # Select the transferred boat
                                new_boat_text = f"{boat_id} - {boat_year} {boat_make} {boat_model}"
                                boat_combo.set(new_boat_text)
                                
                                messagebox.showinfo("Success", f"Boat ownership transferred successfully!")
                                dialog.destroy()
                            except Exception as transfer_error:
                                messagebox.showerror("Error", f"Failed to transfer ownership: {transfer_error}")
                    else:
                        messagebox.showerror("Error", f"A boat with VIN '{vin}' already exists!")
                else:
                    messagebox.showerror("Error", f"Failed to add boat: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add boat: {e}")
        
        tk.Button(dialog, text="Add Boat", command=save, bg='#5cb85c', fg='white').grid(row=7, column=0, columnspan=2, pady=20)
    
    def quick_add_engine_dialog(self, boat_var, engine_combo):
        """Quick-add engine dialog for ticket creation."""
        if not boat_var.get():
            messagebox.showerror("Error", "Please select a boat first")
            return
        
        boat_id = int(boat_var.get().split(' - ')[0])
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Engine")
        dialog.geometry("400x400")
        
        tk.Label(dialog, text="Engine Type:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        engine_type_var = tk.StringVar()
        engine_type_combo = ttk.Combobox(dialog, textvariable=engine_type_var, 
                                         values=['Inboard', 'Outboard', 'Sterndrive', 'PWC'], 
                                         width=28, state='readonly')
        engine_type_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Make:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        make_entry = tk.Entry(dialog, width=30)
        make_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Model:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        model_entry = tk.Entry(dialog, width=30)
        model_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="HP:*").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        hp_entry = tk.Entry(dialog, width=30)
        hp_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Serial Number:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        serial_entry = tk.Entry(dialog, width=30)
        serial_entry.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Year:").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        year_entry = tk.Entry(dialog, width=30)
        year_entry.grid(row=5, column=1, padx=5, pady=5)
        
        # Outdrive field (only for sterndrive engines)
        outdrive_label = tk.Label(dialog, text="Outdrive:")
        outdrive_entry = tk.Entry(dialog, width=30)
        
        def on_engine_type_change(*args):
            """Show/hide outdrive field based on engine type."""
            if engine_type_var.get() == 'Sterndrive':
                outdrive_label.grid(row=6, column=0, sticky='e', padx=5, pady=5)
                outdrive_entry.grid(row=6, column=1, padx=5, pady=5)
            else:
                outdrive_label.grid_remove()
                outdrive_entry.grid_remove()
        
        engine_type_var.trace('w', on_engine_type_change)
        
        def save():
            engine_type = engine_type_var.get().strip()
            make = make_entry.get().strip()
            model = model_entry.get().strip()
            hp = hp_entry.get().strip()
            
            if not engine_type or not make or not model or not hp:
                messagebox.showerror("Error", "Engine Type, Make, Model, and HP are required")
                return
            
            # Validate HP as float
            valid, error = service.validate_positive_number(hp, "HP", allow_zero=False)
            if not valid:
                messagebox.showerror("Validation Error", error)
                return
            
            try:
                # Insert engine into database
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO Engines (boat_id, engine_type, make, model, hp, serial_number, year, outdrive)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (boat_id, engine_type, make, model, float(hp), 
                      serial_entry.get().strip() or None,
                      int(year_entry.get().strip()) if year_entry.get().strip() else None,
                      outdrive_entry.get().strip() if engine_type == 'Sterndrive' else None))
                conn.commit()
                engine_id = cur.lastrowid
                conn.close()
                
                # Refresh engine dropdown
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("SELECT engine_id, engine_type, make, model, hp FROM Engines WHERE boat_id = ?", (boat_id,))
                engines = [f"{e[0]} - {e[2]} {e[3]} ({e[4]} HP {e[1]})" for e in cur.fetchall()]
                conn.close()
                
                engine_combo['values'] = engines
                # Select the newly added engine
                new_engine_text = f"{engine_id} - {make} {model} ({hp} HP {engine_type})"
                engine_combo.set(new_engine_text)
                
                messagebox.showinfo("Success", f"Engine added successfully!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add engine: {e}")
        
        tk.Button(dialog, text="Add Engine", command=save, bg='#5cb85c', fg='white').grid(row=7, column=0, columnspan=2, pady=20)
    
    def add_part_to_ticket(self, ticket_id, parent_dialog):
        """Add part to ticket from detail view."""
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Part to Ticket")
        dialog.geometry("450x250")
        
        tk.Label(dialog, text="Part:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        parts = service.list_parts()
        part_choices = [f"{p['part_id']} - {p['name']} (${p['price']:.2f})" for p in parts]
        part_var = tk.StringVar()
        
        part_frame = tk.Frame(dialog)
        part_frame.grid(row=0, column=1, padx=5, pady=5)
        part_combo = ttk.Combobox(part_frame, textvariable=part_var, values=part_choices, width=33)
        part_combo.pack(side='left')
        tk.Button(part_frame, text="+ Add Part", bg='#5cb85c', fg='white',
                 command=lambda: self.quick_add_part_to_ticket(part_var, part_combo)).pack(side='left', padx=(5, 0))
        
        tk.Label(dialog, text="Quantity:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        qty_entry = tk.Entry(dialog, width=42)
        qty_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Price Override:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        price_entry = tk.Entry(dialog, width=42)
        price_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(dialog, text="(Leave blank to use default price)", font=('Segoe UI', 8), fg='gray').grid(row=3, column=1, sticky='w', padx=5)
        
        def save():
            if not part_var.get() or not qty_entry.get():
                messagebox.showerror("Error", "Part and Quantity are required")
                return
            
            try:
                part_id = int(part_var.get().split(' - ')[0])
                quantity = int(qty_entry.get().strip())
                price_override = float(price_entry.get().strip()) if price_entry.get().strip() else None
                
                service.add_ticket_part(ticket_id, part_id, quantity, price_override)
                try:
                    service.calculate_ticket_totals(ticket_id)
                except Exception as calc_err:
                    print(f"Warning: failed to recalc totals: {calc_err}")
                messagebox.showinfo("Success", "Part added to ticket")
                dialog.destroy()
                parent_dialog.destroy()
                self.show_tickets()
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity or price")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add part: {e}")
        
        tk.Button(dialog, text="Add Part", command=save, bg='#5cb85c', fg='white').grid(row=4, column=0, columnspan=2, pady=20)
    
    def add_labor_to_ticket(self, ticket_id, parent_dialog):
        """Add labor to ticket from detail view."""
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Labor to Ticket")
        dialog.geometry("450x350")
        
        tk.Label(dialog, text="Mechanic:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        
        # Get mechanics from database
        import sqlite3
        conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
        cur = conn.cursor()
        cur.execute("SELECT mechanic_id, name, hourly_rate FROM Mechanics ORDER BY name")
        mechanics = cur.fetchall()
        conn.close()
        
        mechanic_choices = [f"{m[0]} - {m[1]} (${m[2]:.2f}/hr)" for m in mechanics]
        mechanic_var = tk.StringVar()
        mechanic_combo = ttk.Combobox(dialog, textvariable=mechanic_var, values=mechanic_choices, width=40)
        mechanic_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Hours:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        hours_entry = tk.Entry(dialog, width=42)
        hours_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Rate Override:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        rate_entry = tk.Entry(dialog, width=42)
        rate_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(dialog, text="(Leave blank to use mechanic's rate)", font=('Segoe UI', 8), fg='gray').grid(row=3, column=1, sticky='w', padx=5)
        
        tk.Label(dialog, text="Work Description:").grid(row=4, column=0, sticky='ne', padx=5, pady=5)
        desc_text = tk.Text(dialog, width=40, height=6)
        desc_text.grid(row=4, column=1, padx=5, pady=5)
        
        def save():
            if not mechanic_var.get() or not hours_entry.get():
                messagebox.showerror("Error", "Mechanic and Hours are required")
                return
            
            try:
                mechanic_id = int(mechanic_var.get().split(' - ')[0])
                hours = float(hours_entry.get().strip())
                rate_override = float(rate_entry.get().strip()) if rate_entry.get().strip() else None
                description = desc_text.get('1.0', 'end').strip()
                
                service.add_ticket_labor(ticket_id, mechanic_id, hours, description or "", rate_override)
                try:
                    service.calculate_ticket_totals(ticket_id)
                except Exception as calc_err:
                    print(f"Warning: failed to recalc totals: {calc_err}")
                messagebox.showinfo("Success", "Labor added to ticket")
                dialog.destroy()
                parent_dialog.destroy()
                self.show_tickets()
            except ValueError:
                messagebox.showerror("Error", "Invalid hours or rate")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add labor: {e}")
        
        tk.Button(dialog, text="Add Labor", command=save, bg='#5cb85c', fg='white').grid(row=5, column=0, columnspan=2, pady=20)
    
    # ========== PHASE 3A: BACKUP & PDF GENERATION ==========
    
    def show_backup_menu(self):
        """Show backup/restore options dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Database Backup & Restore")
        dialog.geometry("600x450")
        
        # Header
        tk.Label(
            dialog,
            text="Database Backup Management",
            font=('Segoe UI', 16, 'bold')
        ).pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="Create Backup Now",
            font=('Segoe UI', 11),
            bg='#5cb85c',
            fg='white',
            command=self.create_manual_backup,
            width=20
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Restore from Backup",
            font=('Segoe UI', 11),
            bg='#f0ad4e',
            fg='white',
            command=self.restore_from_backup,
            width=20
        ).pack(side='left', padx=5)
        
        # Backup list
        tk.Label(
            dialog,
            text="Available Backups:",
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor='w', padx=20, pady=(20, 5))
        
        list_frame = tk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        backup_tree = ttk.Treeview(
            list_frame,
            columns=('Filename', 'Date', 'Size'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=backup_tree.yview)
        
        backup_tree.heading('Filename', text='Filename')
        backup_tree.heading('Date', text='Date Created')
        backup_tree.heading('Size', text='Size (MB)')
        
        backup_tree.column('Filename', width=300)
        backup_tree.column('Date', width=150)
        backup_tree.column('Size', width=100)
        
        backup_tree.pack(fill='both', expand=True)
        
        # Load backups
        backups = service.list_backups()
        for filename, date, size in backups:
            backup_tree.insert('', 'end', values=(filename, date, f"{size:.2f}"))
        
        tk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def create_manual_backup(self):
        """Create a manual backup."""
        success, backup_path, error = service.create_backup()
        if success:
            messagebox.showinfo("Success", f"Backup created successfully!\n\nLocation: {backup_path}")
        else:
            messagebox.showerror("Error", f"Backup failed: {error}")
    
    def restore_from_backup(self):
        """Restore database from selected backup."""
        backups = service.list_backups()
        if not backups:
            messagebox.showwarning("No Backups", "No backup files found.")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Backup to Restore")
        dialog.geometry("500x300")
        
        tk.Label(
            dialog,
            text="⚠️ WARNING: This will replace your current database!",
            font=('Segoe UI', 11, 'bold'),
            fg='red'
        ).pack(pady=10)
        
        tk.Label(dialog, text="Select backup file:").pack(anchor='w', padx=20)
        
        backup_list = tk.Listbox(dialog, width=70, height=10)
        backup_list.pack(padx=20, pady=10)
        
        for filename, date, size in backups:
            backup_list.insert('end', f"{filename} - {date} ({size:.2f} MB)")
        
        def do_restore():
            selection = backup_list.curselection()
            if not selection:
                messagebox.showerror("Error", "Please select a backup file")
                return
            
            filename = backups[selection[0]][0]
            
            confirm = messagebox.askyesno(
                "Confirm Restore",
                f"Are you sure you want to restore from:\n\n{filename}\n\nThis will replace your current database!",
                icon='warning'
            )
            
            if confirm:
                success, error = service.restore_backup(filename)
                if success:
                    messagebox.showinfo("Success", "Database restored successfully!\n\nPlease restart the application.")
                    dialog.destroy()
                    self.root.quit()
                else:
                    messagebox.showerror("Error", f"Restore failed: {error}")
        
        tk.Button(dialog, text="Restore Selected", command=do_restore, bg='#f0ad4e', fg='white').pack(pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def print_ticket_pdf(self, ticket_id):
        """Generate and save ticket PDF."""
        try:
            details = service.get_ticket_details(ticket_id)
            if not details:
                messagebox.showerror("Error", "Ticket not found")
                return
            
            customer = service.get_customer(details['customer_id'])
            # Get boat info from database if needed
            boat = self.fetch_boat_by_id(details.get('boat_id'))
            
            # Ask user where to save
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"Invoice_{ticket_id}.pdf"
            )
            
            if filename:
                # Map field names expected by PDF generator
                details['date_created'] = details.get('date_opened')
                details['date_completed'] = details.get('date_closed') or 'In Progress'
                # Attach deposits converted to expected keys
                deposits = service.get_ticket_deposits(ticket_id)
                details['deposits'] = [
                    {
                        'date_paid': d.get('payment_date'),
                        'payment_method': d.get('payment_method', ''),
                        'amount': d.get('amount', 0.0)
                    } for d in deposits
                ]
                # Try to get new engine if engine_id exists
                engine = None
                if details.get('engine_id'):
                    try:
                        engine = service.get_new_engine(details['engine_id'])
                    except Exception:
                        engine = None
                pdf_generator.generate_ticket_pdf(details, customer, boat, filename, engine=engine)
                messagebox.showinfo("Success", f"Invoice PDF saved to:\n{filename}")
                
                # Ask if they want to open it
                if messagebox.askyesno("Open PDF", "Would you like to open the PDF now?"):
                    os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")
    
    def print_estimate_pdf(self, estimate_id):
        """Generate and save estimate PDF."""
        try:
            details = service.get_estimate_details(estimate_id)
            if not details:
                messagebox.showerror("Error", "Estimate not found")
                return
            
            customer = service.get_customer(details['customer_id'])
            
            # Get boat and engine info if available
            boat = self.fetch_boat_by_id(details.get('boat_id'))
            engine = self.fetch_engine_by_id(details.get('engine_id'))
            
            # Ask user where to save
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"Estimate_{estimate_id}.pdf"
            )
            
            if filename:
                pdf_generator.generate_estimate_pdf(details, customer, filename, boat=boat, engine=engine)
                messagebox.showinfo("Success", f"Estimate PDF saved to:\n{filename}")
                
                # Ask if they want to open it
                if messagebox.askyesno("Open PDF", "Would you like to open the PDF now?"):
                    os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")
    
    def quick_add_part_to_ticket(self, part_var, part_combo):
        """Quick-add part dialog for ticket parts."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Part")
        dialog.geometry("500x500")
    
        tk.Label(dialog, text="Part Number:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        part_number_entry = tk.Entry(dialog, width=40)
        part_number_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Part Name:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        name_entry = tk.Entry(dialog, width=40)
        name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Stock Quantity:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        stock_entry = tk.Entry(dialog, width=40)
        stock_entry.grid(row=2, column=1, padx=5, pady=5)
        stock_entry.insert(0, "0")
        
        tk.Label(dialog, text="Retail Price:*").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        price_entry = tk.Entry(dialog, width=40)
        price_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Supplier:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        supplier_entry = tk.Entry(dialog, width=40)
        supplier_entry.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Cost from Supplier:").grid(row=5, column=0, sticky='e', padx=5, pady=5)
        cost_entry = tk.Entry(dialog, width=40)
        cost_entry.grid(row=5, column=1, padx=5, pady=5)
        
        taxable_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="Taxable", variable=taxable_var).grid(row=6, column=1, sticky='w', padx=5, pady=5)
        
        def save():
            part_number = part_number_entry.get().strip() or None
            name = name_entry.get().strip()
            stock = stock_entry.get().strip()
            price = price_entry.get().strip()
            
            if not name or not stock or not price:
                messagebox.showerror("Error", "Part Name, Stock, and Retail Price are required")
                return
            
            try:
                supplier = supplier_entry.get().strip() or ""
                cost = float(cost_entry.get().strip()) if cost_entry.get().strip() else 0.0
                
                part_id = service.create_part(part_number, name, int(stock), float(price), supplier, cost, float(price), taxable_var.get())
                
                # Refresh part dropdown
                parts = service.list_parts()
                part_choices = [f"{p['part_id']} - {p['name']} (${p['price']:.2f})" for p in parts]
                part_combo['values'] = part_choices
                part_var.set(f"{part_id} - {name} (${price})")
                
                messagebox.showinfo("Success", "Part added successfully!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add part: {e}")
        
        tk.Button(dialog, text="Add Part", command=save, bg='#5cb85c', fg='white').grid(row=7, column=0, columnspan=2, pady=20)
    
    def show_settings(self):
        """Show settings page with password protection."""
        # Password protection
        password = simpledialog.askstring("Password Required", "Enter password to access settings:", show='*')
        if password != "Cajun":
            messagebox.showerror("Access Denied", "Incorrect password")
            return
        
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header,
            text="Settings",
            font=('Segoe UI', 20, 'bold'),
            bg='white'
        ).pack(side='left')
        
        # Tabs
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill='both', expand=True)
        
        # Mechanics tab
        mechanics_frame = tk.Frame(notebook)
        notebook.add(mechanics_frame, text='Mechanics')
        
        # Mechanics header
        mech_header = tk.Frame(mechanics_frame, bg='white')
        mech_header.pack(fill='x', pady=(0, 10))
        
        tk.Button(
            mech_header,
            text="+ Add Mechanic",
            font=('Segoe UI', 11),
            bg='#5cb85c',
            fg='white',
            command=self.add_mechanic_dialog
        ).pack(side='right')
        
        # Mechanics list
        mech_tree = ttk.Treeview(mechanics_frame, columns=('ID', 'Name', 'Rate', 'Phone', 'Email'), show='headings', height=15)
        mech_tree.heading('ID', text='ID')
        mech_tree.heading('Name', text='Name')
        mech_tree.heading('Rate', text='Hourly Rate')
        mech_tree.heading('Phone', text='Phone')
        mech_tree.heading('Email', text='Email')
        
        mech_tree.column('ID', width=50)
        mech_tree.column('Name', width=200)
        mech_tree.column('Rate', width=100)
        mech_tree.column('Phone', width=120)
        mech_tree.column('Email', width=200)
        
        mech_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Load mechanics
        import sqlite3
        conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
        cur = conn.cursor()
        cur.execute("SELECT mechanic_id, name, hourly_rate, phone, email FROM Mechanics ORDER BY name")
        mechanics = cur.fetchall()
        conn.close()
        
        for mech in mechanics:
            mech_tree.insert('', 'end', values=(
                mech[0],
                mech[1],
                f"${mech[2]:.2f}",
                mech[3] or 'N/A',
                mech[4] or 'N/A'
            ))
        
        # Buttons
        btn_frame = tk.Frame(mechanics_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Edit", command=lambda: self.edit_mechanic_dialog(mech_tree), 
                 bg='#2d6a9f', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text="Delete", command=lambda: self.delete_mechanic(mech_tree), 
                 bg='#d9534f', fg='white').pack(side='left', padx=5)

        # Labor Rates tab
        rates_frame = tk.Frame(notebook)
        notebook.add(rates_frame, text='Labor Rates')

        tk.Label(rates_frame, text="Set labor rates per engine class:", font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10,5))

        form = tk.Frame(rates_frame)
        form.pack(anchor='w', padx=10, pady=5)

        tk.Label(form, text="Outboard ($/hr):").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        out_entry = tk.Entry(form, width=10)
        out_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Inboard ($/hr):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        inb_entry = tk.Entry(form, width=10)
        inb_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="Sterndrive ($/hr):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        ster_entry = tk.Entry(form, width=10)
        ster_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form, text="PWC ($/hr):").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        pwc_entry = tk.Entry(form, width=10)
        pwc_entry.grid(row=3, column=1, padx=5, pady=5)

        # Load existing or defaults
        try:
            import sqlite3
            conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS LaborRates (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    outboard REAL NOT NULL,
                    inboard REAL NOT NULL,
                    sterndrive REAL NOT NULL,
                    pwc REAL NOT NULL
                )
            """)
            conn.commit()
            cur.execute("SELECT outboard, inboard, sterndrive, pwc FROM LaborRates WHERE id = 1")
            row = cur.fetchone()
            if not row:
                # Defaults: Outboard 100, Inboard 120, Sterndrive 120, PWC 120
                cur.execute("INSERT INTO LaborRates (id, outboard, inboard, sterndrive, pwc) VALUES (1, 100.0, 120.0, 120.0, 120.0)")
                conn.commit()
                row = (100.0, 120.0, 120.0, 120.0)
            conn.close()
            out_entry.insert(0, str(row[0]))
            inb_entry.insert(0, str(row[1]))
            ster_entry.insert(0, str(row[2]))
            pwc_entry.insert(0, str(row[3]))
        except Exception as e:
            tk.Label(rates_frame, text=f"Error loading rates: {e}", fg='red').pack(anchor='w', padx=10)

        def save_rates():
            try:
                out = float(out_entry.get().strip())
                inb = float(inb_entry.get().strip())
                ster = float(ster_entry.get().strip())
                pwc = float(pwc_entry.get().strip())
                import sqlite3
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("UPDATE LaborRates SET outboard = ?, inboard = ?, sterndrive = ?, pwc = ? WHERE id = 1", (out, inb, ster, pwc))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Labor rates saved")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save rates: {e}")

        tk.Button(rates_frame, text="Save Rates", command=save_rates, bg='#5cb85c', fg='white').pack(anchor='w', padx=10, pady=10)

        # Financial Reports tab
        reports_frame = tk.Frame(notebook)
        notebook.add(reports_frame, text='Financial Reports')

        # Create scrollable canvas for reports
        canvas = tk.Canvas(reports_frame, bg='white')
        scrollbar_reports = ttk.Scrollbar(reports_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_reports.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_reports.pack(side="right", fill="y")

        tk.Label(scrollable_frame, text="Financial Summary", font=('Segoe UI', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=(10, 5))

        # Get financial data
        import sqlite3
        from datetime import datetime, timedelta
        conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
        cur = conn.cursor()

        # Monthly tax collected
        today = datetime.now()
        first_of_month = today.replace(day=1).strftime('%Y-%m-%d')
        cur.execute("""
            SELECT COALESCE(SUM(tax_amount), 0) as total_tax
            FROM Tickets
            WHERE date_opened >= ? AND status = 'Closed'
        """, (first_of_month,))
        monthly_tax = cur.fetchone()[0]

        # Tax section
        tax_frame = tk.LabelFrame(scrollable_frame, text="Tax Collection (Current Month)", font=('Segoe UI', 11, 'bold'), bg='white', padx=10, pady=10)
        tax_frame.pack(fill='x', padx=10, pady=10)
        tk.Label(tax_frame, text=f"Total Tax Collected: ${monthly_tax:.2f}", font=('Segoe UI', 12), bg='white', fg='#2d6a9f').pack(anchor='w')

        # Mechanic earnings section
        mech_frame = tk.LabelFrame(scrollable_frame, text="Mechanic Earnings", font=('Segoe UI', 11, 'bold'), bg='white', padx=10, pady=10)
        mech_frame.pack(fill='x', padx=10, pady=10)

        # Get all mechanics
        cur.execute("SELECT mechanic_id, name, hourly_rate FROM Mechanics ORDER BY name")
        mechanics_list = cur.fetchall()

        # Week range
        week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        
        for mech in mechanics_list:
            mech_id, mech_name, mech_rate = mech
            
            # This week earnings
            cur.execute("""
                SELECT COALESCE(SUM(ta.hours_worked * ta.labor_rate), 0) as week_total
                FROM TicketAssignments ta
                JOIN Tickets t ON ta.ticket_id = t.ticket_id
                WHERE ta.mechanic_id = ? AND t.date_opened >= ?
            """, (mech_id, week_start))
            week_earnings = cur.fetchone()[0]

            # Total historical earnings
            cur.execute("""
                SELECT COALESCE(SUM(ta.hours_worked * ta.labor_rate), 0) as total_earnings
                FROM TicketAssignments ta
                WHERE ta.mechanic_id = ?
            """, (mech_id,))
            total_earnings = cur.fetchone()[0]

            # Mechanic pay (using their hourly rate)
            cur.execute("""
                SELECT COALESCE(SUM(ta.hours_worked * ?), 0) as week_pay
                FROM TicketAssignments ta
                JOIN Tickets t ON ta.ticket_id = t.ticket_id
                WHERE ta.mechanic_id = ? AND t.date_opened >= ?
            """, (mech_rate, mech_id, week_start))
            week_pay = cur.fetchone()[0]

            cur.execute("""
                SELECT COALESCE(SUM(ta.hours_worked * ?), 0) as total_pay
                FROM TicketAssignments ta
                WHERE ta.mechanic_id = ?
            """, (mech_rate, mech_id))
            total_pay = cur.fetchone()[0]

            mech_detail = tk.Frame(mech_frame, bg='white')
            mech_detail.pack(fill='x', pady=5)
            
            tk.Label(mech_detail, text=f"• {mech_name}", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
            tk.Label(mech_detail, text=f"  This Week - Billed: ${week_earnings:.2f} | Paid: ${week_pay:.2f} | Shop Profit: ${week_earnings - week_pay:.2f}", 
                    font=('Segoe UI', 9), bg='white', fg='#555').pack(anchor='w', padx=15)
            tk.Label(mech_detail, text=f"  All Time - Billed: ${total_earnings:.2f} | Paid: ${total_pay:.2f} | Shop Profit: ${total_earnings - total_pay:.2f}", 
                    font=('Segoe UI', 9), bg='white', fg='#555').pack(anchor='w', padx=15)

        # Parts profit section
        parts_frame = tk.LabelFrame(scrollable_frame, text="Parts Profit", font=('Segoe UI', 11, 'bold'), bg='white', padx=10, pady=10)
        parts_frame.pack(fill='x', padx=10, pady=10)

        # Calculate parts profit
        cur.execute("""
            SELECT 
                COALESCE(SUM(tp.quantity_used * p.price), 0) as parts_revenue,
                COALESCE(SUM(tp.quantity_used * COALESCE(p.cost_from_supplier, 0)), 0) as parts_cost
            FROM TicketParts tp
            JOIN Parts p ON tp.part_id = p.part_id
            JOIN Tickets t ON tp.ticket_id = t.ticket_id
            WHERE t.status = 'Closed'
        """)
        parts_revenue, parts_cost = cur.fetchone()
        parts_profit = parts_revenue - parts_cost

        tk.Label(parts_frame, text=f"Total Parts Revenue: ${parts_revenue:.2f}", font=('Segoe UI', 10), bg='white').pack(anchor='w')
        tk.Label(parts_frame, text=f"Total Parts Cost: ${parts_cost:.2f}", font=('Segoe UI', 10), bg='white').pack(anchor='w')
        tk.Label(parts_frame, text=f"Total Parts Profit: ${parts_profit:.2f}", font=('Segoe UI', 10, 'bold'), bg='white', fg='#5cb85c' if parts_profit > 0 else '#d9534f').pack(anchor='w')

        # Overall shop summary
        summary_frame = tk.LabelFrame(scrollable_frame, text="Shop Summary (All Time)", font=('Segoe UI', 11, 'bold'), bg='white', padx=10, pady=10)
        summary_frame.pack(fill='x', padx=10, pady=10)

        # Total labor billed vs mechanic pay
        cur.execute("""
            SELECT COALESCE(SUM(ta.hours_worked * ta.labor_rate), 0) as total_billed
            FROM TicketAssignments ta
        """)
        total_labor_billed = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(ta.hours_worked * m.hourly_rate), 0) as total_paid
            FROM TicketAssignments ta
            JOIN Mechanics m ON ta.mechanic_id = m.mechanic_id
        """)
        total_labor_paid = cur.fetchone()[0]

        labor_profit = total_labor_billed - total_labor_paid

        tk.Label(summary_frame, text=f"Labor Revenue: ${total_labor_billed:.2f}", font=('Segoe UI', 10), bg='white').pack(anchor='w')
        tk.Label(summary_frame, text=f"Labor Cost (Mechanic Pay): ${total_labor_paid:.2f}", font=('Segoe UI', 10), bg='white').pack(anchor='w')
        tk.Label(summary_frame, text=f"Labor Profit: ${labor_profit:.2f}", font=('Segoe UI', 10, 'bold'), bg='white', fg='#5cb85c' if labor_profit > 0 else '#d9534f').pack(anchor='w')
        
        tk.Label(summary_frame, text="", bg='white').pack()  # Spacer
        
        tk.Label(summary_frame, text=f"Parts Profit: ${parts_profit:.2f}", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
        tk.Label(summary_frame, text=f"Total Shop Profit (Labor + Parts): ${labor_profit + parts_profit:.2f}", 
                font=('Segoe UI', 12, 'bold'), bg='white', fg='#2d6a9f').pack(anchor='w', pady=(5, 0))

        conn.close()
    
    def add_mechanic_dialog(self):
        """Add new mechanic."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Mechanic")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Name:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        name_entry = tk.Entry(dialog, width=35)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Hourly Rate:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        rate_entry = tk.Entry(dialog, width=35)
        rate_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Phone:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        phone_entry = tk.Entry(dialog, width=35)
        phone_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Email:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        email_entry = tk.Entry(dialog, width=35)
        email_entry.grid(row=3, column=1, padx=5, pady=5)
        
        def save():
            name = name_entry.get().strip()
            rate = rate_entry.get().strip()
            
            if not name or not rate:
                messagebox.showerror("Error", "Name and Hourly Rate are required")
                return
            
            try:
                import sqlite3
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO Mechanics (name, hourly_rate, phone, email)
                    VALUES (?, ?, ?, ?)
                """, (name, float(rate), phone_entry.get().strip() or None, email_entry.get().strip() or None))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Mechanic added successfully!")
                dialog.destroy()
                self.show_settings()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add mechanic: {e}")
        
        tk.Button(dialog, text="Add Mechanic", command=save, bg='#5cb85c', fg='white').grid(row=4, column=0, columnspan=2, pady=20)
    
    def edit_mechanic_dialog(self, tree):
        """Edit selected mechanic."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mechanic to edit")
            return
        
        mechanic_id = tree.item(selection[0])['values'][0]
        
        # Get current mechanic data
        import sqlite3
        conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
        cur = conn.cursor()
        cur.execute("SELECT name, hourly_rate, phone, email FROM Mechanics WHERE mechanic_id = ?", (mechanic_id,))
        mech = cur.fetchone()
        conn.close()
        
        if not mech:
            messagebox.showerror("Error", "Mechanic not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Mechanic")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Name:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        name_entry = tk.Entry(dialog, width=35)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, mech[0])
        
        tk.Label(dialog, text="Hourly Rate:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        rate_entry = tk.Entry(dialog, width=35)
        rate_entry.grid(row=1, column=1, padx=5, pady=5)
        rate_entry.insert(0, str(mech[1]))
        
        tk.Label(dialog, text="Phone:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        phone_entry = tk.Entry(dialog, width=35)
        phone_entry.grid(row=2, column=1, padx=5, pady=5)
        phone_entry.insert(0, mech[2] or '')
        
        tk.Label(dialog, text="Email:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        email_entry = tk.Entry(dialog, width=35)
        email_entry.grid(row=3, column=1, padx=5, pady=5)
        email_entry.insert(0, mech[3] or '')
        
        def save():
            name = name_entry.get().strip()
            rate = rate_entry.get().strip()
            
            if not name or not rate:
                messagebox.showerror("Error", "Name and Hourly Rate are required")
                return
            
            try:
                conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
                cur = conn.cursor()
                cur.execute("""
                    UPDATE Mechanics 
                    SET name = ?, hourly_rate = ?, phone = ?, email = ?
                    WHERE mechanic_id = ?
                """, (name, float(rate), phone_entry.get().strip() or None, 
                     email_entry.get().strip() or None, mechanic_id))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Mechanic updated successfully!")
                dialog.destroy()
                self.show_settings()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update mechanic: {e}")
        
        tk.Button(dialog, text="Save Changes", command=save, bg='#5cb85c', fg='white').grid(row=4, column=0, columnspan=2, pady=20)
    
    def delete_mechanic(self, tree):
        """Delete selected mechanic."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mechanic to delete")
            return
        
        mechanic_id = tree.item(selection[0])['values'][0]
        mechanic_name = tree.item(selection[0])['values'][1]
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete mechanic '{mechanic_name}'?"):
            return
        
        try:
            import sqlite3
            conn = sqlite3.connect(service.get_db_path(), timeout=10.0)
            cur = conn.cursor()
            cur.execute("DELETE FROM Mechanics WHERE mechanic_id = ?", (mechanic_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Mechanic deleted successfully!")
            self.show_settings()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete mechanic: {e}")


def main():
    root = tk.Tk()
    app = CajunMarineApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
