import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from db.db_utils import get_db_path


class BoatForm(tk.Frame):
	def __init__(self, master=None, db_path=None, **kwargs):
		super().__init__(master, **kwargs)
		self.master = master
		self.db_path = db_path or get_db_path()
		self.customers = []  # list of (id, name)
		self.create_widgets()
		self.load_customers()

	def create_widgets(self):
		tk.Label(self, text="Create new boat", font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 8))

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
