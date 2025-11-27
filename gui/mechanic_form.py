import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from db.db_utils import get_db_path


class MechanicForm(tk.Frame):
	"""Form to create and manage Mechanics."""
	def __init__(self, master=None, db_path=None, **kwargs):
		super().__init__(master, **kwargs)
		self.master = master
		self.db_path = db_path or get_db_path()
		self.create_widgets()
		self.load_mechanics()

	def create_widgets(self):
		tk.Label(self, text="Mechanics — Create / Edit", font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 8))

		# Mechanics list (table)
		self.tree = ttk.Treeview(self, columns=('id', 'name', 'hourly_rate'), show='headings', height=6)
		self.tree.heading('id', text='ID')
		self.tree.heading('name', text='Name')
		self.tree.heading('hourly_rate', text='Hourly Rate')
		self.tree.column('id', width=40, anchor='center')
		self.tree.column('name', width=180)
		self.tree.column('hourly_rate', width=110)
		self.tree.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=(0,6))

		self.tree_scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.tree_scroll.set)
		self.tree_scroll.grid(row=1, column=3, sticky='ns')

		self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

		# Name (required)
		tk.Label(self, text="Name *").grid(row=2, column=0, sticky='e', padx=(0,6))
		self.name_entry = tk.Entry(self, width=40)
		self.name_entry.grid(row=2, column=1, sticky='w')

		# Hourly Rate (required)
		tk.Label(self, text="Hourly Rate *").grid(row=3, column=0, sticky='e', padx=(0,6))
		self.rate_entry = tk.Entry(self, width=20)
		self.rate_entry.grid(row=3, column=1, sticky='w')

		# Buttons
		btn_frame = tk.Frame(self)
		btn_frame.grid(row=4, column=0, columnspan=2, pady=(8,0))

		self.create_btn = tk.Button(btn_frame, text="Create", command=self.on_create, width=12)
		self.create_btn.pack(side='left', padx=(0,6))

		clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear_form, width=12)
		clear_btn.pack(side='left')

		self.update_btn = tk.Button(btn_frame, text='Update', command=self.on_update, width=12)
		self.update_btn.pack(side='left', padx=(6,0))

		self.delete_btn = tk.Button(btn_frame, text='Delete', command=self.on_delete, width=12)
		self.delete_btn.pack(side='left', padx=(6,0))

		self.message_label = tk.Label(self, text="", fg='red')
		self.message_label.grid(row=5, column=0, columnspan=3, pady=(6,0))

	def clear_form(self):
		self.name_entry.delete(0, tk.END)
		self.rate_entry.delete(0, tk.END)
		self.editing_mechanic_id = None
		try:
			self.create_btn.config(state='normal')
		except Exception:
			pass

	def validate_inputs(self, name, rate):
		if not name.strip():
			return False, "Name is required"
		try:
			float(rate)
		except Exception:
			return False, "Hourly rate must be a number"
		return True, None

	def on_create(self):
		name = self.name_entry.get()
		rate = self.rate_entry.get()
		valid, msg = self.validate_inputs(name, rate)
		if not valid:
			messagebox.showerror("Invalid input", msg)
			return
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute(
				"INSERT INTO Mechanics (name, hourly_rate) VALUES (?, ?)",
				(name.strip(), float(rate)),
			)
			conn.commit()
			mid = cur.lastrowid
			conn.close()
			messagebox.showinfo("Success", f"Mechanic created (id={mid}).")
			self.clear_form()
			self.load_mechanics()
		except Exception as e:
			messagebox.showerror('Error', f'Failed to create mechanic: {e}')

	def load_mechanics(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT mechanic_id, name, hourly_rate FROM Mechanics ORDER BY mechanic_id')
			rows = cur.fetchall()
			conn.close()
			for r in self.tree.get_children():
				self.tree.delete(r)
			for r in rows:
				self.tree.insert('', 'end', values=(r[0], r[1], r[2]))
		except Exception as e:
			self.message_label.config(text=f'Failed to load mechanics: {e}')

	def on_tree_select(self, event):
		sel = self.tree.selection()
		if not sel:
			return
		vals = self.tree.item(sel[0])['values']
		if not vals:
			return
		mid, name, rate = vals
		self.name_entry.delete(0, tk.END)
		self.name_entry.insert(0, name)
		self.rate_entry.delete(0, tk.END)
		self.rate_entry.insert(0, rate)
		self.editing_mechanic_id = mid
		try:
			self.create_btn.config(state='disabled')
		except Exception:
			pass

	def on_update(self):
		if not hasattr(self, 'editing_mechanic_id') or not self.editing_mechanic_id:
			messagebox.showwarning('No selection', 'Select a mechanic from the list to update.')
			return
		name = self.name_entry.get()
		rate = self.rate_entry.get()
		valid, msg = self.validate_inputs(name, rate)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('UPDATE Mechanics SET name=?, hourly_rate=? WHERE mechanic_id=?', (name.strip(), float(rate), self.editing_mechanic_id))
			conn.commit()
			conn.close()
			messagebox.showinfo('Success', f'Mechanic updated (id={self.editing_mechanic_id}).')
			self.clear_form()
			self.load_mechanics()
		except Exception as e:
			messagebox.showerror('Error', f'Failed to update mechanic: {e}')

	def on_delete(self):
		sel = self.tree.selection()
		if not sel:
			messagebox.showwarning('No selection', 'Select a mechanic from the list to delete.')
			return
		vals = self.tree.item(sel[0])['values']
		mid = vals[0]
		if not messagebox.askyesno('Confirm delete', f'Are you sure you want to delete mechanic id {mid}?'):
			return
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('DELETE FROM Mechanics WHERE mechanic_id = ?', (mid,))
			conn.commit()
			conn.close()
			messagebox.showinfo('Deleted', f'Mechanic id {mid} deleted.')
			self.clear_form()
			self.load_mechanics()
		except Exception as e:
			messagebox.showerror('Error', f'Failed to delete mechanic: {e}')
