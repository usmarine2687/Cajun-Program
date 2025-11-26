import os
import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


def get_db_path():
	# Ensure DB is located in same folder as this script
	base_dir = os.path.dirname(os.path.abspath(__file__))
	return os.path.join(base_dir, "Cajun_Data.db")


def ensure_engine_columns(db_path: str):
	"""Ensure Engines table has the required columns (type, make, model, hp, serial_number).
	Adds missing columns using ALTER TABLE when possible (SQLite supports ADD COLUMN).
	This makes the running DB compatible with the updated schema.
	"""
	conn = sqlite3.connect(db_path)
	cur = conn.cursor()
	cur.execute("PRAGMA table_info(Engines)")
	cols = {r[1] for r in cur.fetchall()}  # column names
	need = []
	if 'type' not in cols:
		need.append(("type", "TEXT"))
	if 'make' not in cols:
		need.append(("make", "TEXT"))
	if 'model' not in cols:
		need.append(("model", "TEXT"))
	if 'hp' not in cols:
		need.append(("hp", "INTEGER"))
	if 'serial_number' not in cols:
		need.append(("serial_number", "TEXT"))

	for name, ctype in need:
		try:
			cur.execute(f"ALTER TABLE Engines ADD COLUMN {name} {ctype}")
		except Exception:
			# best-effort; ignore errors (e.g., table missing)
			pass

	conn.commit()
	conn.close()


class CustomerForm(tk.Frame):
	def __init__(self, master=None, db_path=None, **kwargs):
		super().__init__(master, **kwargs)
		self.master = master
		self.db_path = db_path or get_db_path()
		self.create_widgets()
		# load customers into the list view
		self.load_customers()

	def create_widgets(self):
		# Title
		tk.Label(self, text="Customers — Create / Edit", font=(None, 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 8))

		# Customers list (table)
		self.tree = ttk.Treeview(self, columns=('id', 'name', 'phone', 'email', 'address'), show='headings', height=6)
		# Make headings clickable to sort. We manage base labels so we can append ▲/▼ icons
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

		# customers scrollbar
		self.tree_scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.tree_scroll.set)
		self.tree_scroll.grid(row=1, column=3, sticky='ns')

		# Bind selection
		self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

		# Name (required)
		tk.Label(self, text="Name *").grid(row=2, column=0, sticky='e', padx=(0,6))
		self.name_entry = tk.Entry(self, width=40)
		self.name_entry.grid(row=2, column=1, sticky='w')

		# Phone
		tk.Label(self, text="Phone").grid(row=3, column=0, sticky='e', padx=(0,6))
		self.phone_entry = tk.Entry(self, width=40)
		self.phone_entry.grid(row=3, column=1, sticky='w')

		# Email
		tk.Label(self, text="Email").grid(row=4, column=0, sticky='e', padx=(0,6))
		self.email_entry = tk.Entry(self, width=40)
		self.email_entry.grid(row=4, column=1, sticky='w')

		# Address
		tk.Label(self, text="Address").grid(row=5, column=0, sticky='ne', padx=(0,6))
		self.address_text = tk.Text(self, width=30, height=4)
		self.address_text.grid(row=5, column=1, sticky='w')

		# Buttons
		btn_frame = tk.Frame(self)
		btn_frame.grid(row=6, column=0, columnspan=2, pady=(8,0))

		self.create_btn = tk.Button(btn_frame, text="Create", command=self.on_create, width=12)
		self.create_btn.pack(side='left', padx=(0,6))

		clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear_form, width=12)
		clear_btn.pack(side='left')

		# Edit / Delete buttons for customers
		self.update_btn = tk.Button(btn_frame, text='Update', command=self.on_update, width=12)
		self.update_btn.pack(side='left', padx=(6,0))

		self.delete_btn = tk.Button(btn_frame, text='Delete', command=self.on_delete, width=12)
		self.delete_btn.pack(side='left', padx=(6,0))

            
	def clear_form(self):
		self.name_entry.delete(0, tk.END)
		self.phone_entry.delete(0, tk.END)
		self.email_entry.delete(0, tk.END)
		self.address_text.delete('1.0', tk.END)
		# exit edit mode and re-enable create button
		self.editing_customer_id = None
		try:
			self.create_btn.config(state='normal')
		except Exception:
			pass

	def validate_inputs(self, name, phone, email):
		if not name.strip():
			return False, "Name is required"

		# Basic email check
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
			# notify listeners (auto-refresh other forms)
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
		except sqlite3.IntegrityError as e:
			messagebox.showerror('DB error', f'Integrity error: {e}')
		except sqlite3.OperationalError as e:
			messagebox.showerror('DB error', f'Operational error: {e}')
		except Exception as e:
			messagebox.showerror('Error', f'An unexpected error occurred: {e}')

	def load_customers(self):
		"""Load customers from DB and populate the Treeview."""
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT customer_id, name, phone, email, address FROM Customers ORDER BY name')
			rows = cur.fetchall()
			conn.close()

			# clear tree
			for r in self.tree.get_children():
				self.tree.delete(r)

			for r in rows:
				self.tree.insert('', 'end', values=(r[0], r[1], r[2] or '', r[3] or '', r[4] or ''))

			# default sort by ID on initial load
			try:
				self.sort_tree('id', reverse=False)
			except Exception:
				pass

		except Exception as e:
			messagebox.showerror('Error', f'Failed to load customers: {e}')

	def on_tree_select(self, event):
		sel = self.tree.selection()
		if not sel:
			return
		vals = self.tree.item(sel[0])['values']
		if not vals:
			return
		cid, name, phone, email, address = vals
		# populate form
		self.name_entry.delete(0, tk.END)
		self.name_entry.insert(0, name)
		self.phone_entry.delete(0, tk.END)
		self.phone_entry.insert(0, phone)
		self.email_entry.delete(0, tk.END)
		self.email_entry.insert(0, email)
		self.address_text.delete('1.0', tk.END)
		self.address_text.insert('1.0', address)

		# mark editing
		self.editing_customer_id = cid
		# disable create button
		try:
			self.create_btn.config(state='disabled')
		except Exception:
			pass

	def sort_tree(self, col, reverse=None):
		"""Sort the customer Treeview by column. Toggle ascending/descending if reverse omitted.
		col: column name (one of 'id', 'name', 'phone', 'email', 'address')
		reverse: if True, sort descending else ascending. Function toggles if called repeatedly.
		"""
		# track sort state on object
		if not hasattr(self, '_sort_state'):
			self._sort_state = {}

		prev = self._sort_state.get(col, False)
		# if reverse is None we toggle; else use the provided bool
		if reverse is None:
			rev = not prev
		else:
			rev = bool(reverse)

		# build list of (value, item)
		items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]

		# convert values to proper types for numeric columns
		if col == 'id':
			def keyfn(x):
				v = x[0]
				try:
					return int(v)
				except Exception:
					return 0
		else:
			def keyfn(x):
				v = x[0]
				return str(v).lower() if v is not None else ""

		items.sort(key=keyfn, reverse=rev)

		# reorder
		for index, (val, k) in enumerate(items):
			self.tree.move(k, '', index)

		# remember new state
		self._sort_state[col] = rev
		# update header visuals (append ▲ for ascending, ▼ for descending)
		arrow = '▲' if not rev else '▼'
		for c, lbl in self._column_labels.items():
			text = lbl
			if c == col:
				text = f"{lbl} {arrow}"
			self.tree.heading(c, text=text)

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
			# Attempt delete (might fail due to FK constraints)
			cur.execute('DELETE FROM Customers WHERE customer_id = ?', (cid,))
			conn.commit()
			conn.close()
			messagebox.showinfo('Deleted', f'Customer id {cid} deleted.')
			self.clear_form()
			self.load_customers()
			# notify other forms
			try:
				self.notify_change()
			except Exception:
				pass
		except sqlite3.IntegrityError as e:
			messagebox.showerror('DB error', f'Integrity error: {e}. Delete related boats/engines first.')
		except Exception as e:
			messagebox.showerror('Error', f'Failed to delete customer: {e}')

	# change listener support so other tabs can auto-refresh when customers change
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


class TicketForm(tk.Frame):
	"""Form to create and manage Tickets (tickets attached to boats/customers)."""
	def __init__(self, master=None, db_path=None, **kwargs):
		super().__init__(master, **kwargs)
		self.master = master
		self.db_path = db_path or get_db_path()
		self.customers = []
		self.boats = []
		self.create_widgets()
		self.load_customers()
		self.load_boats()
		self.load_tickets()

	def create_widgets(self):
		tk.Label(self, text="Create / Edit Tickets", font=(None, 14, 'bold')).grid(row=0, column=0, columnspan=4, pady=(0,8))

		# --- Filters ---
		# Row 1: status + customer search
		tk.Label(self, text='Status').grid(row=1, column=0, sticky='e', padx=(0,6))
		self.status_filter = ttk.Combobox(self, state='readonly', values=['All','Open','In Progress','Closed'], width=12)
		self.status_filter.grid(row=1, column=1, sticky='w')
		self.status_filter.set('All')

		tk.Label(self, text='Customer (contains)').grid(row=1, column=2, sticky='e', padx=(6,6))
		self.customer_filter_entry = tk.Entry(self, width=28)
		self.customer_filter_entry.grid(row=1, column=3, sticky='w')

		# Row 2: boat + opened date range
		tk.Label(self, text='Boat (contains)').grid(row=2, column=0, sticky='e', padx=(0,6))
		self.boat_filter_entry = tk.Entry(self, width=28)
		self.boat_filter_entry.grid(row=2, column=1, sticky='w')

		tk.Label(self, text='Opened from (YYYY-MM-DD)').grid(row=2, column=2, sticky='e', padx=(6,6))
		self.opened_from_entry = tk.Entry(self, width=18)
		self.opened_from_entry.grid(row=2, column=3, sticky='w')

		# Row 3: opened to + closed range + filter buttons
		tk.Label(self, text='Opened to (YYYY-MM-DD)').grid(row=3, column=0, sticky='e', padx=(0,6))
		self.opened_to_entry = tk.Entry(self, width=18)
		self.opened_to_entry.grid(row=3, column=1, sticky='w')

		tk.Label(self, text='Closed from (YYYY-MM-DD)').grid(row=3, column=2, sticky='e', padx=(6,6))
		self.closed_from_entry = tk.Entry(self, width=18)
		self.closed_from_entry.grid(row=3, column=3, sticky='w')

		# Row 4: closed to + buttons
		tk.Label(self, text='Closed to (YYYY-MM-DD)').grid(row=4, column=0, sticky='e', padx=(0,6))
		self.closed_to_entry = tk.Entry(self, width=18)
		self.closed_to_entry.grid(row=4, column=1, sticky='w')

		btn_filt_frame = tk.Frame(self)
		btn_filt_frame.grid(row=4, column=2, columnspan=2, sticky='w')
		apply_btn = tk.Button(btn_filt_frame, text='Apply filters', command=self.apply_filters, width=12)
		apply_btn.pack(side='left', padx=(0,6))
		clear_btn = tk.Button(btn_filt_frame, text='Clear filters', command=self.clear_filters, width=12)
		clear_btn.pack(side='left')

		# Tickets list
		self.tree = ttk.Treeview(self, columns=('id','status','customer','boat','opened','closed','description'), show='headings', height=6)
		self.tree.heading('id', text='ID')
		self.tree.heading('status', text='Status')
		self.tree.heading('customer', text='Customer')
		self.tree.heading('boat', text='Boat')
		self.tree.heading('opened', text='Opened')
		self.tree.heading('closed', text='Closed')
		self.tree.heading('description', text='Description')
		self.tree.column('id', width=50, anchor='center')
		self.tree.column('status', width=100)
		self.tree.column('customer', width=160)
		self.tree.column('boat', width=160)
		self.tree.column('opened', width=80)
		self.tree.column('closed', width=80)
		self.tree.column('description', width=260)
		self.tree.grid(row=5, column=0, columnspan=4, sticky='nsew', padx=(0,6))

		scr = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=scr.set)
		scr.grid(row=5, column=4, sticky='ns')

		self.tree.bind('<<TreeviewSelect>>', self.on_tree_select_ticket)

		# Customer selector
		lbl = tk.Label(self, text='Customer *')
		lbl.grid(row=6, column=0, sticky='e', padx=(0,6))
		self.customer_combo = ttk.Combobox(self, state='readonly', width=48)
		self.customer_combo.grid(row=6, column=1, sticky='w')

		# refresh
		refresh_btn = tk.Button(self, text='Refresh', command=lambda: (self.load_customers(), self.load_boats(), self.load_tickets()), width=8)
		refresh_btn.grid(row=6, column=2, padx=(6,0))

		# Boat selector
		tk.Label(self, text='Boat *').grid(row=7, column=0, sticky='e', padx=(0,6))
		self.boat_combo = ttk.Combobox(self, state='readonly', width=48)
		self.boat_combo.grid(row=7, column=1, sticky='w')

		# Status
		tk.Label(self, text='Status').grid(row=8, column=0, sticky='e', padx=(0,6))
		self.status_combo = ttk.Combobox(self, state='readonly', values=['Open','In Progress','Closed'], width=20)
		self.status_combo.grid(row=8, column=1, sticky='w')
		self.status_combo.set('Open')

		# Description
		tk.Label(self, text='Description').grid(row=9, column=0, sticky='ne', padx=(0,6))
		self.desc_text = tk.Text(self, width=60, height=6)
		self.desc_text.grid(row=9, column=1, columnspan=2, sticky='w')

		# Date closed (optional)
		tk.Label(self, text='Date closed (YYYY-MM-DD)').grid(row=10, column=0, sticky='e', padx=(0,6))
		self.closed_entry = tk.Entry(self, width=20)
		self.closed_entry.grid(row=10, column=1, sticky='w')

		# Buttons
		btn_frame = tk.Frame(self)
		btn_frame.grid(row=11, column=0, columnspan=3, pady=(8,0))

		self.create_btn = tk.Button(btn_frame, text='Create', command=self.on_create, width=12)
		self.create_btn.pack(side='left', padx=(0,6))
		self.update_btn = tk.Button(btn_frame, text='Update', command=self.on_update, width=12)
		self.update_btn.pack(side='left', padx=(6,0))
		self.delete_btn = tk.Button(btn_frame, text='Delete', command=self.on_delete, width=12)
		self.delete_btn.pack(side='left', padx=(6,0))

		self.message_label = tk.Label(self, text='', fg='red')
		self.message_label.grid(row=12, column=0, columnspan=3, pady=(6,0))

	def load_customers(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT customer_id, name FROM Customers ORDER BY name')
			rows = cur.fetchall()
			conn.close()
			self.customers = rows
			vals = [f"{r[0]} - {r[1]}" for r in rows]
			self.customer_combo['values'] = vals
			if vals:
				self.customer_combo.current(0)
			self.message_label.config(text='')
		except Exception as e:
			self.message_label.config(text=f'Error loading customers: {e}')

	def load_boats(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT boat_id, make, model FROM Boats ORDER BY boat_id')
			rows = cur.fetchall()
			conn.close()
			self.boats = rows
			vals = [f"{r[0]} - {r[1] or ''} {r[2] or ''}".strip() for r in rows]
			self.boat_combo['values'] = vals
			if vals:
				self.boat_combo.current(0)
			self.message_label.config(text='')
		except Exception as e:
			self.message_label.config(text=f'Error loading boats: {e}')

	def clear_form(self):
		self.customer_combo.set('')
		self.boat_combo.set('')
		self.status_combo.set('Open')
		self.desc_text.delete('1.0', tk.END)
		self.closed_entry.delete(0, tk.END)
		self.editing_ticket_id = None
		try:
			self.create_btn.config(state='normal')
		except Exception:
			pass

	def validate_inputs(self, cust_val, boat_val, status_val):
		if not cust_val:
			return False, 'Please select a customer'
		if not boat_val:
			return False, 'Please select a boat'
		if status_val and status_val not in ['Open','In Progress','Closed']:
			return False, 'Invalid status'
		# date closed if present must be YYYY-MM-DD
		closed = self.closed_entry.get().strip()
		if closed:
			parts = closed.split('-')
			if len(parts) != 3 or not all(p.isdigit() for p in parts):
				return False, 'Date closed must be YYYY-MM-DD or blank'
		return True, None

	def on_create(self):
		cust_val = self.customer_combo.get()
		boat_val = self.boat_combo.get()
		status_val = self.status_combo.get()
		desc = self.desc_text.get('1.0', tk.END).strip()
		closed_val = self.closed_entry.get().strip() or None

		valid, msg = self.validate_inputs(cust_val, boat_val, status_val)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return

		try:
			cust_id = int(cust_val.split(' - ')[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse selected customer id.')
			return
		try:
			boat_id = int(boat_val.split(' - ')[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse selected boat id.')
			return

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('INSERT INTO Tickets (customer_id, boat_id, description, status, date_closed) VALUES (?, ?, ?, ?, ?)',
				(cust_id, boat_id, desc if desc else None, status_val, closed_val))
			conn.commit()
			tid = cur.lastrowid
			conn.close()
			messagebox.showinfo('Success', f'Ticket created (id={tid}).')
			self.clear_form()
			self.load_tickets()
			try:
				self.notify_change()
			except Exception:
				pass
		except Exception as e:
			messagebox.showerror('Error', f'Failed to create ticket: {e}')

	def load_tickets(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()

			# Build filter-aware query
			query = 'SELECT t.ticket_id, t.status, c.name, b.make, b.model, t.date_opened, t.date_closed, t.description, t.boat_id FROM Tickets t LEFT JOIN Customers c ON t.customer_id=c.customer_id LEFT JOIN Boats b ON t.boat_id=b.boat_id'
			clauses = []
			params = []

			# status filter
			status_f = getattr(self, 'status_filter', None)
			if status_f:
				val = status_f.get().strip()
				if val and val != 'All':
					clauses.append('t.status = ?')
					params.append(val)

			# customer filter (substring on customer name)
			cust_txt = (getattr(self, 'customer_filter_entry', None).get() if getattr(self, 'customer_filter_entry', None) else '').strip()
			if cust_txt:
				clauses.append('c.name LIKE ?')
				params.append(f'%{cust_txt}%')

			# boat filter (substring on make+model)
			boat_txt = (getattr(self, 'boat_filter_entry', None).get() if getattr(self, 'boat_filter_entry', None) else '').strip()
			if boat_txt:
				clauses.append("(COALESCE(b.make,'') || ' ' || COALESCE(b.model,'')) LIKE ?")
				params.append(f'%{boat_txt}%')

			# opened date range
			opened_from = (getattr(self, 'opened_from_entry', None).get().strip() if getattr(self, 'opened_from_entry', None) else '')
			opened_to = (getattr(self, 'opened_to_entry', None).get().strip() if getattr(self, 'opened_to_entry', None) else '')
			if opened_from:
				clauses.append('t.date_opened >= ?')
				params.append(opened_from)
			if opened_to:
				clauses.append('t.date_opened <= ?')
				params.append(opened_to)

			# closed date range
			closed_from = (getattr(self, 'closed_from_entry', None).get().strip() if getattr(self, 'closed_from_entry', None) else '')
			closed_to = (getattr(self, 'closed_to_entry', None).get().strip() if getattr(self, 'closed_to_entry', None) else '')
			if closed_from:
				clauses.append('t.date_closed >= ?')
				params.append(closed_from)
			if closed_to:
				clauses.append('t.date_closed <= ?')
				params.append(closed_to)

			if clauses:
				query = query + ' WHERE ' + ' AND '.join(clauses)

			query = query + ' ORDER BY t.ticket_id'
			cur.execute(query, params)
			rows = cur.fetchall()
			conn.close()

			# clear tree
			for iid in self.tree.get_children():
				self.tree.delete(iid)
			for r in rows:
				# (ticket_id, status, cust_name, make, model, opened, closed, desc, boat_id)
				tid, status, cname, bmake, bmodel, opened, closed, desc, boat_id = r
				boat_label = f"{boat_id} - {bmake or ''} {bmodel or ''}".strip()
				self.tree.insert('', 'end', values=(tid, status or '', cname or '', boat_label, opened or '', closed or '', (desc or '')[:200]))
		except Exception as e:
			self.message_label.config(text=f'Error loading tickets: {e}')

	def on_tree_select_ticket(self, event):
		sel = self.tree.selection()
		if not sel:
			return
		vals = self.tree.item(sel[0])['values']
		if not vals:
			return
		tid = vals[0]
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT ticket_id, customer_id, boat_id, description, status, date_closed FROM Tickets WHERE ticket_id = ?', (tid,))
			row = cur.fetchone()
			conn.close()
			if not row:
				return
			_tid, cust_id, boat_id, desc, status, date_closed = row
			# set customer
			for idx, c in enumerate(self.customer_combo['values']):
				if str(cust_id) == str(c).split(' - ')[0]:
					self.customer_combo.current(idx)
					break
			# set boat
			for idx, b in enumerate(self.boat_combo['values']):
				if str(boat_id) == str(b).split(' - ')[0]:
					self.boat_combo.current(idx)
					break
			self.status_combo.set(status or 'Open')
			self.desc_text.delete('1.0', tk.END)
			if desc:
				self.desc_text.insert('1.0', desc)
			self.closed_entry.delete(0, tk.END)
			if date_closed:
				self.closed_entry.insert(0, date_closed)
			self.editing_ticket_id = tid
			try:
				self.create_btn.config(state='disabled')
			except Exception:
				pass
		except Exception as e:
			messagebox.showerror('Error', f'Failed to load ticket for editing: {e}')

	def on_update(self):
		if not hasattr(self, 'editing_ticket_id') or not self.editing_ticket_id:
			messagebox.showwarning('No selection', 'Select a ticket from the list to update.')
			return
		cust_val = self.customer_combo.get()
		boat_val = self.boat_combo.get()
		status_val = self.status_combo.get()
		desc = self.desc_text.get('1.0', tk.END).strip()
		closed_val = self.closed_entry.get().strip() or None

		valid, msg = self.validate_inputs(cust_val, boat_val, status_val)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return
		try:
			cust_id = int(cust_val.split(' - ')[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse customer id.')
			return
		try:
			boat_id = int(boat_val.split(' - ')[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse boat id.')
			return

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('UPDATE Tickets SET customer_id=?, boat_id=?, description=?, status=?, date_closed=? WHERE ticket_id=?',
				(cust_id, boat_id, desc if desc else None, status_val, closed_val, self.editing_ticket_id))
			conn.commit()
			conn.close()
			messagebox.showinfo('Success', f'Ticket updated (id={self.editing_ticket_id}).')
			self.clear_form()
			self.load_tickets()
			try:
				self.notify_change()
			except Exception:
				pass
		except Exception as e:
			messagebox.showerror('Error', f'Failed to update ticket: {e}')

	def on_delete(self):
		sel = self.tree.selection()
		if not sel:
			messagebox.showwarning('No selection', 'Select a ticket from the list to delete.')
			return
		vals = self.tree.item(sel[0])['values']
		if not vals:
			messagebox.showwarning('No selection', 'Select a ticket from the list to delete.')
			return
		try:
			tid = int(vals[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse ticket id.')
			return
		if not messagebox.askyesno('Confirm delete', f'Are you sure you want to delete ticket id {tid}?'):
			return
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('DELETE FROM Tickets WHERE ticket_id = ?', (tid,))
			conn.commit()
			conn.close()
			messagebox.showinfo('Deleted', f'Ticket id {tid} deleted.')
			self.clear_form()
			self.load_tickets()
			try:
				self.notify_change()
			except Exception:
				pass
		except Exception as e:
			messagebox.showerror('Error', f'Failed to delete ticket: {e}')

	# change listener support
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

	def apply_filters(self):
		"""Validate filter inputs (dates) then reload tickets using current filter values."""
		# basic date format check (YYYY-MM-DD)
		for name, entry in (('Opened from', getattr(self, 'opened_from_entry', None)), ('Opened to', getattr(self, 'opened_to_entry', None)), ('Closed from', getattr(self, 'closed_from_entry', None)), ('Closed to', getattr(self, 'closed_to_entry', None))):
			if entry:
				val = entry.get().strip()
				if val:
					parts = val.split('-')
					if len(parts) != 3 or not all(p.isdigit() for p in parts):
						messagebox.showerror('Invalid date', f'{name} must be YYYY-MM-DD or blank')
						return
		self.load_tickets()

	def clear_filters(self):
		if getattr(self, 'status_filter', None):
			self.status_filter.set('All')
		for entry in ('customer_filter_entry', 'boat_filter_entry', 'opened_from_entry', 'opened_to_entry', 'closed_from_entry', 'closed_to_entry'):
			w = getattr(self, entry, None)
			if w:
				w.delete(0, tk.END)
		self.load_tickets()


class BoatForm(tk.Frame):
	def __init__(self, master=None, db_path=None, **kwargs):
		super().__init__(master, **kwargs)
		self.master = master
		self.db_path = db_path or get_db_path()
		self.customers = []  # list of (id, name)
		self.create_widgets()
		self.load_customers()

	def create_widgets(self):
		tk.Label(self, text="Create new boat", font=(None, 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 8))

		# Customer selector
		tk.Label(self, text="Customer *").grid(row=1, column=0, sticky='e', padx=(0,6))
		self.customer_combo = ttk.Combobox(self, state='readonly', width=37)
		self.customer_combo.grid(row=1, column=1, sticky='w')

		refresh_btn = tk.Button(self, text="Refresh", command=self.load_customers, width=8)
		refresh_btn.grid(row=1, column=2, padx=(6,0))

		# Make
		tk.Label(self, text="Make").grid(row=2, column=0, sticky='e', padx=(0,6))
		self.make_entry = tk.Entry(self, width=40)
		self.make_entry.grid(row=2, column=1, sticky='w')

		# Model
		tk.Label(self, text="Model").grid(row=3, column=0, sticky='e', padx=(0,6))
		self.model_entry = tk.Entry(self, width=40)
		self.model_entry.grid(row=3, column=1, sticky='w')

		# Year
		tk.Label(self, text="Year").grid(row=4, column=0, sticky='e', padx=(0,6))
		self.year_entry = tk.Entry(self, width=40)
		self.year_entry.grid(row=4, column=1, sticky='w')

		# Buttons
		btn_frame = tk.Frame(self)
		btn_frame.grid(row=5, column=0, columnspan=3, pady=(8,0))

		create_btn = tk.Button(btn_frame, text="Create", command=self.on_create, width=12)
		create_btn.pack(side='left', padx=(0,6))

		clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear_form, width=12)
		clear_btn.pack(side='left')

		# Message area
		self.message_label = tk.Label(self, text="", fg='red')
		self.message_label.grid(row=6, column=0, columnspan=3, pady=(6,0))

	def load_customers(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT customer_id, name FROM Customers ORDER BY name')
			rows = cur.fetchall()
			conn.close()

			if not rows:
				self.customers = []
				self.customer_combo['values'] = []
				self.customer_combo.set('')
				self.message_label.config(text='No customers found — add a customer in the Customers tab.')
				return

			self.customers = rows
			values = [f"{r[0]} - {r[1]}" for r in rows]
			self.customer_combo['values'] = values
			# Select first by default
			if values:
				self.customer_combo.current(0)
			self.message_label.config(text='')
		except Exception as e:
			self.message_label.config(text=f'Error loading customers: {e}')

	def clear_form(self):
		self.customer_combo.set('')
		self.make_entry.delete(0, tk.END)
		self.model_entry.delete(0, tk.END)
		self.year_entry.delete(0, tk.END)
		self.message_label.config(text='')

	def validate_inputs(self, customer_val, make, model, year):
		if not customer_val:
			return False, 'Please select a customer (required)'

		# Year if provided must be an integer
		if year:
			try:
				y = int(year)
				if y < 1000 or y > 9999:
					return False, 'Please enter a realistic 4-digit year or leave blank'
			except ValueError:
				return False, 'Year must be a number (e.g. 2005) or left blank'

		return True, None

	def on_create(self):
		customer_val = self.customer_combo.get()
		make = self.make_entry.get()
		model = self.model_entry.get()
		year = self.year_entry.get()

		valid, msg = self.validate_inputs(customer_val, make, model, year)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return

		# Parse selected customer id
		try:
			cust_id = int(customer_val.split(' - ')[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse selected customer id.')
			return

		# Insert into Boats
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute(
				'INSERT INTO Boats (customer_id, make, model, year) VALUES (?, ?, ?, ?)',
				(cust_id, make.strip() if make else None, model.strip() if model else None, int(year) if year else None),
			)
			conn.commit()
			boat_id = cur.lastrowid
			conn.close()

			messagebox.showinfo('Success', f'Boat created (id={boat_id}).')
			self.clear_form()
			# notify listeners (auto-refresh other forms)
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


class EngineForm(tk.Frame):
	"""Form to add engines attached to boats (boat_id foreign key)."""
	def __init__(self, master=None, db_path=None, **kwargs):
		super().__init__(master, **kwargs)
		self.master = master
		self.db_path = db_path or get_db_path()
		self.boats = []  # list of (boat_id, make, model, customer_id)
		self.create_widgets()
		self.load_boats()
		self.load_engines()

	def create_widgets(self):
		tk.Label(self, text="Create / Edit engines", font=(None, 14, 'bold')).grid(row=0, column=0, columnspan=4, pady=(0, 8))

		# Engines list (table) — pick an engine to edit
		self.engine_tree = ttk.Treeview(self, columns=('id', 'boat', 'type', 'make', 'model', 'hp', 'serial'), show='headings', height=6)
		self.engine_tree.heading('id', text='ID')
		self.engine_tree.heading('boat', text='Boat')
		self.engine_tree.heading('type', text='Type')
		self.engine_tree.heading('make', text='Make')
		self.engine_tree.heading('model', text='Model')
		self.engine_tree.heading('hp', text='HP')
		self.engine_tree.heading('serial', text='Serial #')
		self.engine_tree.column('id', width=50, anchor='center')
		self.engine_tree.column('boat', width=170)
		self.engine_tree.column('type', width=100)
		self.engine_tree.column('make', width=110)
		self.engine_tree.column('model', width=110)
		self.engine_tree.column('hp', width=60)
		self.engine_tree.column('serial', width=140)
		self.engine_tree.grid(row=1, column=0, columnspan=4, padx=(0,6), sticky='nsew')

		self.engine_tree_scroll = ttk.Scrollbar(self, orient='vertical', command=self.engine_tree.yview)
		self.engine_tree.configure(yscrollcommand=self.engine_tree_scroll.set)
		self.engine_tree_scroll.grid(row=1, column=4, sticky='ns')

		self.engine_tree.bind('<<TreeviewSelect>>', self.on_tree_select_engine)


		# Boat selector (moved below the list so it doesn't overlap the tree)
		tk.Label(self, text="Boat *").grid(row=2, column=0, sticky='e', padx=(0,6))
		self.boat_combo = ttk.Combobox(self, state='readonly', width=50)
		self.boat_combo.grid(row=2, column=1, sticky='w')

		refresh_btn = tk.Button(self, text="Refresh", command=lambda: (self.load_boats(), self.load_engines()), width=8)
		refresh_btn.grid(row=2, column=2, padx=(6,0))

		# Type
		tk.Label(self, text="Type").grid(row=3, column=0, sticky='e', padx=(0,6))
		self.type_entry = tk.Entry(self, width=40)
		self.type_entry.grid(row=3, column=1, sticky='w')

		# Make
		tk.Label(self, text="Make").grid(row=4, column=0, sticky='e', padx=(0,6))
		self.make_entry = tk.Entry(self, width=40)
		self.make_entry.grid(row=4, column=1, sticky='w')

		# Model
		tk.Label(self, text="Model").grid(row=5, column=0, sticky='e', padx=(0,6))
		self.model_entry = tk.Entry(self, width=40)
		self.model_entry.grid(row=5, column=1, sticky='w')

		# HP
		tk.Label(self, text="HP").grid(row=6, column=0, sticky='e', padx=(0,6))
		self.hp_entry = tk.Entry(self, width=12)
		self.hp_entry.grid(row=6, column=1, sticky='w')

		# Serial Number
		tk.Label(self, text="Serial #").grid(row=7, column=0, sticky='e', padx=(0,6))
		self.serial_entry = tk.Entry(self, width=40)
		self.serial_entry.grid(row=7, column=1, sticky='w')

		# Buttons (create / update / delete)
		btn_frame = tk.Frame(self)
		btn_frame.grid(row=8, column=0, columnspan=3, pady=(8,0))

		self.create_btn = tk.Button(btn_frame, text="Create", command=self.on_create, width=12)
		self.create_btn.pack(side='left', padx=(0,6))

		self.update_btn = tk.Button(btn_frame, text="Update", command=self.on_update, width=12)
		self.update_btn.pack(side='left', padx=(0,6))

		self.delete_btn = tk.Button(btn_frame, text="Delete", command=self.on_delete, width=12)
		self.delete_btn.pack(side='left')

		self.message_label = tk.Label(self, text="", fg='red')
		self.message_label.grid(row=9, column=0, columnspan=3, pady=(6,0))

	def load_boats(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			# Query boats and include customer name for helpful display if available
			cur.execute("SELECT b.boat_id, b.make, b.model, c.name FROM Boats b LEFT JOIN Customers c ON b.customer_id = c.customer_id ORDER BY b.boat_id")
			rows = cur.fetchall()
			conn.close()

			if not rows:
				self.boats = []
				self.boat_combo['values'] = []
				self.boat_combo.set('')
				self.message_label.config(text='No boats found — add a boat first.')
				return

			self.boats = rows
			values = [f"{r[0]} - {r[1] or ''} {r[2] or ''} (cust: {r[3] or 'unknown'})".strip() for r in rows]
			self.boat_combo['values'] = values
			if values:
				self.boat_combo.current(0)
			self.message_label.config(text='')

			# also refresh engine list since boats changed
			try:
				self.load_engines()
			except Exception:
				pass

		except Exception as e:
			self.message_label.config(text=f'Error loading boats: {e}')

	def clear_form(self):
		self.boat_combo.set('')
		self.type_entry.delete(0, tk.END)
		self.make_entry.delete(0, tk.END)
		self.model_entry.delete(0, tk.END)
		self.hp_entry.delete(0, tk.END)
		self.serial_entry.delete(0, tk.END)
		self.message_label.config(text='')
		# exit any edit mode
		self.editing_engine_id = None
		self.create_btn.config(state='normal')

	def validate_inputs(self, boat_val, type_val, serial_val):
		if not boat_val:
			return False, 'Please select a boat (required)'

		# Serial number optional but if present ensure not blank
		if serial_val and not serial_val.strip():
			return False, 'Serial number cannot be only whitespace'

		return True, None

	def validate_engine_fields(self, boat_val, type_val, make_val, model_val, hp_val, serial_val):
		# boat required
		if not boat_val:
			return False, 'Please select a boat (required)'
		# HP numeric if present
		if hp_val:
			try:
				int(hp_val)
			except Exception:
				return False, 'HP must be a number (integer) or left blank'
		# serial optional but not only whitespace
		if serial_val and not serial_val.strip():
			return False, 'Serial number cannot be only whitespace'
		return True, None

	def on_create(self):
		boat_val = self.boat_combo.get()
		type_val = self.type_entry.get()
		make_val = self.make_entry.get()
		model_val = self.model_entry.get()
		hp_val = self.hp_entry.get()
		serial_val = self.serial_entry.get()

		valid, msg = self.validate_engine_fields(boat_val, type_val, make_val, model_val, hp_val, serial_val)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return

		try:
			boat_id = int(boat_val.split(' - ')[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse selected boat id.')
			return

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute(
				'INSERT INTO Engines (boat_id, type, make, model, hp, serial_number) VALUES (?, ?, ?, ?, ?, ?)',
				(
					boat_id,
					type_val.strip() if type_val else None,
					make_val.strip() if make_val else None,
					model_val.strip() if model_val else None,
					int(hp_val) if hp_val else None,
					serial_val.strip() if serial_val else None,
				),
			)
			conn.commit()
			engine_id = cur.lastrowid
			conn.close()

			messagebox.showinfo('Success', f'Engine created (id={engine_id}).')
			self.clear_form()
			self.load_engines()
			# notify listeners (if any)
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

	# --- Engines list methods ---
	def load_engines(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute("SELECT e.engine_id, e.boat_id, e.type, e.make, e.model, e.hp, e.serial_number, b.make AS boat_make, b.model AS boat_model, c.name AS cust_name FROM Engines e LEFT JOIN Boats b ON e.boat_id=b.boat_id LEFT JOIN Customers c ON b.customer_id=c.customer_id ORDER BY e.engine_id")
			rows = cur.fetchall()
			conn.close()

			# populate engine tree
			self.engines = rows
			# clear existing
			for iid in self.engine_tree.get_children():
				self.engine_tree.delete(iid)

			for r in rows:
				# r = (engine_id, boat_id, type, make, model, hp, serial_number, boat_make, boat_model, cust_name)
				engine_id, boat_id, etype, emake, emodel, ehp, serial, boat_make, boat_model, cust = r
				boat_label = f"{boat_id} - {boat_make or ''} {boat_model or ''} ({cust or 'unknown'})"
				self.engine_tree.insert('', 'end', values=(engine_id, boat_label, etype or '', emake or '', emodel or '', ehp or '', serial or ''))
		except Exception as e:
			self.message_label.config(text=f'Error loading engines: {e}')

	def on_tree_select_engine(self, event):
		sel = self.engine_tree.selection()
		if not sel:
			return
		vals = self.engine_tree.item(sel[0])['values']
		if not vals:
			return
		engine_id = vals[0]

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT engine_id, boat_id, type, make, model, hp, serial_number FROM Engines WHERE engine_id = ?', (engine_id,))
			row = cur.fetchone()
			conn.close()
			if not row:
				return
			eid, boat_id, etype, emake, emodel, ehp, serial = row

			# set boat selection if present
			for idx, b in enumerate(self.boat_combo['values']):
				if str(boat_id) == str(b).split(' - ')[0]:
					self.boat_combo.current(idx)
					break

			# populate fields
			self.type_entry.delete(0, tk.END)
			if etype:
				self.type_entry.insert(0, etype)
			self.make_entry = getattr(self, 'make_entry', None)
			if not self.make_entry:
				self.make_entry = tk.Entry(self, width=30)
			self.make_entry.delete(0, tk.END)
			if emake:
				self.make_entry.insert(0, emake)
			self.model_entry = getattr(self, 'model_entry', None)
			if not self.model_entry:
				self.model_entry = tk.Entry(self, width=30)
			self.model_entry.delete(0, tk.END)
			if emodel:
				self.model_entry.insert(0, emodel)
			# hp
			self.hp_entry = getattr(self, 'hp_entry', None)
			if not self.hp_entry:
				self.hp_entry = tk.Entry(self, width=10)
			self.hp_entry.delete(0, tk.END)
			if ehp is not None:
				self.hp_entry.insert(0, str(ehp))

			self.serial_entry.delete(0, tk.END)
			if serial:
				self.serial_entry.insert(0, serial)

			self.editing_engine_id = engine_id
			try:
				self.create_btn.config(state='disabled')
			except Exception:
				pass
		except Exception as e:
			messagebox.showerror('Error', f'Failed to load engine for editing: {e}')

	def on_update(self):
		if not hasattr(self, 'editing_engine_id') or not self.editing_engine_id:
			messagebox.showwarning('No selection', 'Select an engine from the list to update.')
			return

		boat_val = self.boat_combo.get()
		type_val = self.type_entry.get()
		make_val = self.make_entry.get()
		model_val = self.model_entry.get()
		hp_val = self.hp_entry.get()
		serial_val = self.serial_entry.get()

		valid, msg = self.validate_engine_fields(boat_val, type_val, make_val, model_val, hp_val, serial_val)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return

		try:
			boat_id = int(boat_val.split(' - ')[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse selected boat id.')
			return

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute(
				'UPDATE Engines SET boat_id=?, type=?, make=?, model=?, hp=?, serial_number=? WHERE engine_id=?',
				(
					boat_id,
					type_val.strip() if type_val else None,
					make_val.strip() if make_val else None,
					model_val.strip() if model_val else None,
					int(hp_val) if hp_val else None,
					serial_val.strip() if serial_val else None,
					self.editing_engine_id,
				),
			)
			conn.commit()
			conn.close()

			messagebox.showinfo('Success', f'Engine updated (id={self.editing_engine_id}).')
			self.clear_form()
			self.load_engines()
			try:
				self.notify_change()
			except Exception:
				pass

		except Exception as e:
			messagebox.showerror('Error', f'Failed to update engine: {e}')

	def on_delete(self):
		sel = self.engine_tree.selection()
		if not sel:
			messagebox.showwarning('No selection', 'Select an engine from the list to delete.')
			return
		vals = self.engine_tree.item(sel[0])['values']
		if not vals:
			messagebox.showwarning('No selection', 'Select an engine from the list to delete.')
			return
		try:
			engine_id = int(vals[0])
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse selected engine id.')
			return
		if not messagebox.askyesno('Confirm delete', f'Are you sure you want to delete engine id {engine_id}?'):
			return
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('DELETE FROM Engines WHERE engine_id = ?', (engine_id,))
			conn.commit()
			conn.close()
			messagebox.showinfo('Deleted', f'Engine id {engine_id} deleted.')
			self.clear_form()
			self.load_engines()
			try:
				self.notify_change()
			except Exception:
				pass
		except sqlite3.IntegrityError as e:
			messagebox.showerror('DB error', f'Integrity error: {e}')
		except sqlite3.OperationalError as e:
			messagebox.showerror('DB error', f'Operational error: {e}')
		except Exception as e:
			messagebox.showerror('Error', f'Failed to delete engine: {e}')

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




def main():
	root = tk.Tk()
	root.title("Cajun Shop — Create Customer / Boat")

	# Notebook with tabs for Customer and Boat
	notebook = ttk.Notebook(root)
	notebook.pack(padx=12, pady=12, fill='both', expand=True)

	cust_frame = CustomerForm(notebook)
	notebook.add(cust_frame, text='Customers')

	# add boats tab (class added below)
	boat_frame = BoatForm(notebook)
	notebook.add(boat_frame, text='Boats')

	# ensure DB schema compatibility (add engine cols if missing) before creating forms
	try:
		ensure_engine_columns(get_db_path())
	except Exception:
		# best-effort; continue even if migration helper fails
		pass

	engine_frame = EngineForm(notebook)
	notebook.add(engine_frame, text='Engines')

	# Tickets tab
	ticket_frame = TicketForm(notebook)
	notebook.add(ticket_frame, text='Tickets')

	# Auto-refresh wiring: when a create/update/delete happens in one form, refresh relevant lists in others
	# Customer changes -> reload Boat customer selector and Engine boat lists
	cust_frame.add_change_listener(lambda: (boat_frame.load_customers(), engine_frame.load_boats(), ticket_frame.load_customers(), ticket_frame.load_tickets()))

	# Boat changes -> reload Engine boat selector and engine list
	boat_frame.add_change_listener(lambda: (engine_frame.load_boats(), engine_frame.load_engines(), ticket_frame.load_boats(), ticket_frame.load_tickets()))
	root.resizable(False, False)
	root.mainloop()


if __name__ == '__main__':
	main()



