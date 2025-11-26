import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from db.db_utils import get_db_path

class CustomerForm(tk.Frame):
    def __init__(self, master=None, db_path=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.db_path = db_path or get_db_path()
        self.create_widgets()
        self.load_customers()

    def create_widgets(self):
        tk.Label(self, text="Customers — Create / Edit", font=(None, 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 8))
        self.tree = ttk.Treeview(self, columns=('id', 'name', 'phone', 'email', 'address'), show='headings', height=6)
        self._column_labels = {'id': 'ID', 'name': 'Name', 'phone': 'Phone', 'email': 'Email', 'address': 'Address'}
        self.tree.heading('id', text=self._column_labels['id'], command=lambda c='id': self.sort_tree(c, reverse=None))
        self.tree.heading('name', text=self._column_labels['name'], command=lambda c='name': self.sort_tree(c, reverse=None))
        self.tree.heading('phone', text=self._column_labels['phone'], command=lambda c='phone': self.sort_tree(c, reverse=None))
        self.tree.heading('email', text=self._column_labels['email'], command=lambda c='email': self.sort_tree(c, reverse=None))
        self.tree.heading('address', text=self._column_labels['address'], command=lambda c='address': self.sort_tree(c, reverse=None))
        self.tree.column('id', width=40, anchor='center')
        self.tree.column('name', width=180)
        self.tree.column('phone', width=110)
        self.tree.column('email', width=180)
        self.tree.column('address', width=250)
        self.tree.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=(0,6))
        self.tree_scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.grid(row=1, column=3, sticky='ns')
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        tk.Label(self, text="Name *").grid(row=2, column=0, sticky='e', padx=(0,6))
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.grid(row=2, column=1, sticky='w')
        tk.Label(self, text="Phone").grid(row=3, column=0, sticky='e', padx=(0,6))
        self.phone_entry = tk.Entry(self, width=40)
        self.phone_entry.grid(row=3, column=1, sticky='w')
        tk.Label(self, text="Email").grid(row=4, column=0, sticky='e', padx=(0,6))
        self.email_entry = tk.Entry(self, width=40)
        self.email_entry.grid(row=4, column=1, sticky='w')
        tk.Label(self, text="Address").grid(row=5, column=0, sticky='ne', padx=(0,6))
        self.address_text = tk.Text(self, width=30, height=4)
        self.address_text.grid(row=5, column=1, sticky='w')
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(8,0))
        self.create_btn = tk.Button(btn_frame, text="Create", command=self.on_create, width=12)
        self.create_btn.pack(side='left', padx=(0,6))
        clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear_form, width=12)
        clear_btn.pack(side='left')
        self.update_btn = tk.Button(btn_frame, text='Update', command=self.on_update, width=12)
        self.update_btn.pack(side='left', padx=(6,0))
        self.delete_btn = tk.Button(btn_frame, text='Delete', command=self.on_delete, width=12)
        self.delete_btn.pack(side='left', padx=(6,0))

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.address_text.delete('1.0', tk.END)
        self.editing_customer_id = None
        try:
            self.create_btn.config(state='normal')
        except Exception:
            pass

    def validate_inputs(self, name, phone, email):
        if not name.strip():
            return False, "Name is required"
        if email and ("@" not in email or "." not in email):
            return False, "Please enter a valid email or leave it blank"
        return True, None

    def on_create(self):
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        email = self.email_entry.get()
        address = self.address_text.get('1.0', tk.END).strip()
        valid, msg = self.validate_inputs(name, phone, email)
        if not valid:
            messagebox.showerror("Invalid input", msg)
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
                (name.strip(), phone.strip() if phone else None, email.strip() if email else None, address if address else None),
            )
            conn.commit()
            customer_id = cur.lastrowid
            conn.close()
            messagebox.showinfo("Success", f"Customer created (id={customer_id}).")
            self.clear_form()
            self.load_customers()
            try:
                self.notify_change()
            except Exception:
                pass
        except sqlite3.IntegrityError as e:
            messagebox.showerror('DB error', f'Integrity error: {e}')
        except sqlite3.OperationalError as e:
            messagebox.showerror('DB error', f'Operational error: {e}')
        except Exception as e:
            messagebox.showerror('Error', f'An unexpected error occurred: {e}')

    def load_customers(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('SELECT customer_id, name, phone, email, address FROM Customers ORDER BY name')
            rows = cur.fetchall()
            conn.close()
            for r in self.tree.get_children():
                self.tree.delete(r)
            for r in rows:
                self.tree.insert('', 'end', values=(r[0], r[1], r[2] or '', r[3] or '', r[4] or ''))
        except Exception as e:
            pass

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        if not vals:
            return
        cid, name, phone, email, address = vals
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, phone)
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, email)
        self.address_text.delete('1.0', tk.END)
        self.address_text.insert('1.0', address)
        self.editing_customer_id = cid
        try:
            self.create_btn.config(state='disabled')
        except Exception:
            pass

    def on_update(self):
        if not hasattr(self, 'editing_customer_id') or not self.editing_customer_id:
            messagebox.showwarning('No selection', 'Select a customer from the list to update.')
            return
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        email = self.email_entry.get()
        address = self.address_text.get('1.0', tk.END).strip()
        valid, msg = self.validate_inputs(name, phone, email)
        if not valid:
            messagebox.showerror('Invalid input', msg)
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('UPDATE Customers SET name=?, phone=?, email=?, address=? WHERE customer_id=?', (name.strip(), phone.strip() if phone else None, email.strip() if email else None, address if address else None, self.editing_customer_id))
            conn.commit()
            conn.close()
            messagebox.showinfo('Success', f'Customer updated (id={self.editing_customer_id}).')
            self.clear_form()
            self.load_customers()
            try:
                self.notify_change()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror('Error', f'Failed to update customer: {e}')

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select a customer from the list to delete.')
            return
        vals = self.tree.item(sel[0])['values']
        cid = vals[0]
        if not messagebox.askyesno('Confirm delete', f'Are you sure you want to delete customer id {cid}?'):
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('DELETE FROM Customers WHERE customer_id = ?', (cid,))
            conn.commit()
            conn.close()
            messagebox.showinfo('Deleted', f'Customer id {cid} deleted.')
            self.clear_form()
            self.load_customers()
            try:
                self.notify_change()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror('Error', f'Failed to delete customer: {e}')

    def sort_tree(self, col, reverse=None):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]) if t[0] else 0, reverse=reverse if reverse is not None else False)
        except Exception:
            l.sort(key=lambda t: t[0], reverse=reverse if reverse is not None else False)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        if reverse is None:
            self.sort_tree(col, reverse=True)

    def add_change_listener(self, fn):
        if not hasattr(self, '_listeners'):
            self._listeners = []
        self._listeners.append(fn)

    def notify_change(self):
        for fn in getattr(self, '_listeners', []):
            try:
                fn()
            except Exception:
                pass
