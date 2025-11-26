import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from db.db_utils import get_db_path


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
		# boat required
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
