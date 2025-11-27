import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from db.db_utils import get_db_path


class TicketAssignmentForm(tk.Frame):
	"""Form to assign mechanics to tickets and track hours worked."""
	def __init__(self, master=None, db_path=None, **kwargs):
		super().__init__(master, **kwargs)
		self.master = master
		self.db_path = db_path or get_db_path()
		self.tickets = []
		self.mechanics = []
		self.create_widgets()
		self.load_tickets()
		self.load_mechanics()
		self.load_assignments()

	def create_widgets(self):
		tk.Label(self, text="Ticket Assignments — Assign Mechanics & Track Hours", font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, columnspan=4, pady=(0, 8))

		# Layout weights so inputs stay visible and table expands
		for c in range(0, 4):
			self.grid_columnconfigure(c, weight=0)
		self.grid_columnconfigure(1, weight=1)
		self.grid_rowconfigure(10, weight=1)

		# Ticket selector
		tk.Label(self, text="Ticket *").grid(row=2, column=0, sticky='e', padx=(0,6))
		self.ticket_combo = ttk.Combobox(self, state='readonly', width=50)
		self.ticket_combo.grid(row=2, column=1, columnspan=2, sticky='w')

		refresh_btn = tk.Button(self, text="Refresh", command=lambda: (self.load_tickets(), self.load_mechanics(), self.load_assignments()), width=8)
		refresh_btn.grid(row=2, column=3, padx=(6,0))

		# Mechanic selector
		tk.Label(self, text="Mechanic *").grid(row=3, column=0, sticky='e', padx=(0,6))
		self.mechanic_combo = ttk.Combobox(self, state='readonly', width=50)
		self.mechanic_combo.grid(row=3, column=1, columnspan=2, sticky='w')

		# Hours worked
		tk.Label(self, text="Hours Worked *").grid(row=4, column=0, sticky='e', padx=(0,6))
		self.hours_entry = tk.Entry(self, width=20)
		self.hours_entry.grid(row=4, column=1, sticky='w')

		# Calculated labor cost (read-only display)
		tk.Label(self, text="Labor Cost").grid(row=5, column=0, sticky='e', padx=(0,6))
		self.cost_label = tk.Label(self, text="$0.00", font=('Segoe UI', 10, 'bold'), fg='green')
		self.cost_label.grid(row=5, column=1, sticky='w')

		# Calculate button
		calc_btn = tk.Button(self, text="Calculate Cost", command=self.calculate_cost, width=15)
		calc_btn.grid(row=5, column=2, padx=(6,0))

		# Work description
		tk.Label(self, text="Work Description").grid(row=6, column=0, sticky='ne', padx=(0,6))
		self.work_desc_text = tk.Text(self, width=60, height=4)
		self.work_desc_text.grid(row=6, column=1, columnspan=2, sticky='nsew')

		# Buttons
		btn_frame = tk.Frame(self)
		btn_frame.grid(row=7, column=0, columnspan=4, pady=(8,0))

		self.create_btn = tk.Button(btn_frame, text="Assign", command=self.on_create, width=12)
		self.create_btn.pack(side='left', padx=(0,6))

		clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear_form, width=12)
		clear_btn.pack(side='left')

		self.update_btn = tk.Button(btn_frame, text='Update', command=self.on_update, width=12)
		self.update_btn.pack(side='left', padx=(6,0))

		self.delete_btn = tk.Button(btn_frame, text='Delete', command=self.on_delete, width=12)
		self.delete_btn.pack(side='left', padx=(6,0))

		self.message_label = tk.Label(self, text="", fg='red')
		self.message_label.grid(row=8, column=0, columnspan=4, pady=(6,0))

		# Filter section
		filter_frame = tk.Frame(self)
		filter_frame.grid(row=9, column=0, columnspan=4, pady=(8,4), sticky='w')
		
		tk.Label(filter_frame, text="Filter by Ticket:", font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(0,6))
		self.filter_ticket_combo = ttk.Combobox(filter_frame, state='readonly', width=50)
		self.filter_ticket_combo.pack(side='left', padx=(0,6))
		
		filter_btn = tk.Button(filter_frame, text="Apply", command=self.apply_filter, width=8)
		filter_btn.pack(side='left', padx=(0,6))
		
		clear_filter_btn = tk.Button(filter_frame, text="Clear", command=self.clear_filter, width=8)
		clear_filter_btn.pack(side='left')

		# Export CSV
		export_btn = tk.Button(filter_frame, text="Export CSV", command=self.export_assignments_csv, width=10)
		export_btn.pack(side='left', padx=(6,0))

		# Assignments list (below inputs)
		self.tree = ttk.Treeview(self, columns=('id', 'ticket', 'mechanic', 'hours', 'labor_cost', 'work'), show='headings', height=8)
		self.tree.heading('id', text='Assignment ID', command=lambda: self.sort_column('id', False))
		self.tree.heading('ticket', text='Ticket', command=lambda: self.sort_column('ticket', False))
		self.tree.heading('mechanic', text='Mechanic', command=lambda: self.sort_column('mechanic', False))
		self.tree.heading('hours', text='Hours Worked', command=lambda: self.sort_column('hours', False))
		self.tree.heading('labor_cost', text='Labor Cost ($)', command=lambda: self.sort_column('labor_cost', False))
		self.tree.heading('work', text='Work Description', command=lambda: self.sort_column('work', False))
		self.tree.column('id', width=100, anchor='center')
		self.tree.column('ticket', width=260)
		self.tree.column('mechanic', width=180)
		self.tree.column('hours', width=100, anchor='center')
		self.tree.column('labor_cost', width=120, anchor='e')
		self.tree.column('work', width=260)
		self.tree.grid(row=10, column=0, columnspan=4, sticky='nsew', padx=(0,6))

		self.tree_scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.tree_scroll.set)
		self.tree_scroll.grid(row=10, column=4, sticky='ns')

		self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
		self.tree.bind('<Double-1>', self.on_tree_double_click)

	def load_tickets(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('''SELECT t.ticket_id, t.status, c.name, b.make, b.model, t.description 
						   FROM Tickets t 
						   LEFT JOIN Customers c ON t.customer_id=c.customer_id 
						   LEFT JOIN Boats b ON t.boat_id=b.boat_id 
						   ORDER BY t.ticket_id''')
			rows = cur.fetchall()
			conn.close()
			self.tickets = rows
			vals = [f"{r[0]} - {r[1]} - {r[2] or 'Unknown'} - {r[3] or ''} {r[4] or ''} - {(r[5] or '')[:30]}" for r in rows]
			self.ticket_combo['values'] = vals
			
			# Populate filter dropdown with 'All' option
			filter_vals = ['All'] + vals
			self.filter_ticket_combo['values'] = filter_vals
			self.filter_ticket_combo.set('All')
			
			if vals:
				self.ticket_combo.current(0)
			self.message_label.config(text='')
		except Exception as e:
			self.message_label.config(text=f'Error loading tickets: {e}')

	def load_mechanics(self):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT mechanic_id, name, hourly_rate FROM Mechanics ORDER BY name')
			rows = cur.fetchall()
			conn.close()
			self.mechanics = rows
			vals = [f"{r[0]} - {r[1]} (${r[2]:.2f}/hr)" for r in rows]
			self.mechanic_combo['values'] = vals
			if vals:
				self.mechanic_combo.current(0)
			self.message_label.config(text='')
		except Exception as e:
			self.message_label.config(text=f'Error loading mechanics: {e}')

	def load_assignments(self, filter_ticket_id=None):
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			
			query = '''SELECT ta.assignment_id, t.ticket_id, t.status, c.name, b.make, b.model, 
					   m.name, m.hourly_rate, ta.hours_worked, ta.work_description
					   FROM TicketAssignments ta
					   JOIN Tickets t ON ta.ticket_id=t.ticket_id
					   JOIN Mechanics m ON ta.mechanic_id=m.mechanic_id
					   LEFT JOIN Customers c ON t.customer_id=c.customer_id
					   LEFT JOIN Boats b ON t.boat_id=b.boat_id'''
			
			if filter_ticket_id:
				query += ' WHERE t.ticket_id = ?'
				cur.execute(query + ' ORDER BY ta.assignment_id DESC', (filter_ticket_id,))
			else:
				cur.execute(query + ' ORDER BY ta.assignment_id DESC')
			
			rows = cur.fetchall()
			conn.close()

			for r in self.tree.get_children():
				self.tree.delete(r)

			for r in rows:
				assignment_id, ticket_id, status, cust_name, boat_make, boat_model, mech_name, hourly_rate, hours, work_desc = r
				ticket_label = f"#{ticket_id} - {status} - {cust_name or 'Unknown'} - {boat_make or ''} {boat_model or ''}".strip()
				labor_cost = (hours or 0) * (hourly_rate or 0)
				trunc = (work_desc or '')
				if len(trunc) > 60:
					trunc = trunc[:57] + '...'
				self.tree.insert('', 'end', values=(assignment_id, ticket_label, mech_name, hours or 0, f"${labor_cost:.2f}", trunc))
		except Exception as e:
			self.message_label.config(text=f'Failed to load assignments: {e}')

	def clear_form(self):
		self.ticket_combo.set('')
		self.mechanic_combo.set('')
		self.hours_entry.delete(0, tk.END)
		try:
			self.work_desc_text.delete('1.0', tk.END)
		except Exception:
			pass
		self.cost_label.config(text='$0.00')
		self.editing_assignment_id = None
		try:
			self.create_btn.config(state='normal')
		except Exception:
			pass

	def calculate_cost(self):
		"""Calculate and display labor cost based on selected mechanic and hours."""
		try:
			mechanic_val = self.mechanic_combo.get()
			hours_val = self.hours_entry.get()
			
			if not mechanic_val or not hours_val:
				self.cost_label.config(text='$0.00')
				return

			# Parse mechanic ID and get rate
			mechanic_id = int(mechanic_val.split(' - ')[0])
			hours = float(hours_val)
			
			# Find mechanic's hourly rate
			rate = 0
			for m in self.mechanics:
				if m[0] == mechanic_id:
					rate = m[2]
					break
			
			cost = hours * rate
			self.cost_label.config(text=f'${cost:.2f}')
		except Exception as e:
			self.cost_label.config(text='Error')
			self.message_label.config(text=f'Calculate error: {e}')

	def validate_inputs(self, ticket_val, mechanic_val, hours_val):
		if not ticket_val:
			return False, 'Please select a ticket'
		if not mechanic_val:
			return False, 'Please select a mechanic'
		if not hours_val:
			return False, 'Hours worked is required'
		try:
			h = float(hours_val)
			if h <= 0:
				return False, 'Hours must be greater than 0'
		except Exception:
			return False, 'Hours must be a valid number'
		return True, None

	def on_create(self):
		ticket_val = self.ticket_combo.get()
		mechanic_val = self.mechanic_combo.get()
		hours_val = self.hours_entry.get()
		work_desc = self.work_desc_text.get('1.0', tk.END).strip()

		valid, msg = self.validate_inputs(ticket_val, mechanic_val, hours_val)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return

		try:
			ticket_id = int(ticket_val.split(' - ')[0])
			mechanic_id = int(mechanic_val.split(' - ')[0])
			hours = float(hours_val)
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse ticket or mechanic ID.')
			return

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('INSERT INTO TicketAssignments (ticket_id, mechanic_id, hours_worked, work_description) VALUES (?, ?, ?, ?)',
					(ticket_id, mechanic_id, hours, work_desc or None))
			conn.commit()
			aid = cur.lastrowid
			conn.close()
			messagebox.showinfo('Success', f'Assignment created (id={aid}).')
			self.clear_form()
			self.load_assignments()
		except Exception as e:
			messagebox.showerror('Error', f'Failed to create assignment: {e}')

	def on_tree_select(self, event):
		sel = self.tree.selection()
		if not sel:
			return
		vals = self.tree.item(sel[0])['values']
		if not vals:
			return
		assignment_id = vals[0]

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT assignment_id, ticket_id, mechanic_id, hours_worked, work_description FROM TicketAssignments WHERE assignment_id = ?', (assignment_id,))
			row = cur.fetchone()
			conn.close()
			if not row:
				return
			aid, ticket_id, mechanic_id, hours, work_desc = row

			# Set ticket selection
			for idx, val in enumerate(self.ticket_combo['values']):
				if str(ticket_id) == str(val).split(' - ')[0]:
					self.ticket_combo.current(idx)
					break

			# Set mechanic selection
			for idx, val in enumerate(self.mechanic_combo['values']):
				if str(mechanic_id) == str(val).split(' - ')[0]:
					self.mechanic_combo.current(idx)
					break

			self.hours_entry.delete(0, tk.END)
			self.hours_entry.insert(0, str(hours or 0))
			self.calculate_cost()
			# Set work description
			try:
				self.work_desc_text.delete('1.0', tk.END)
				self.work_desc_text.insert('1.0', (work_desc or ''))
			except Exception:
				pass

			self.editing_assignment_id = assignment_id
			try:
				self.create_btn.config(state='disabled')
			except Exception:
				pass
		except Exception as e:
			messagebox.showerror('Error', f'Failed to load assignment for editing: {e}')

	def on_update(self):
		if not hasattr(self, 'editing_assignment_id') or not self.editing_assignment_id:
			messagebox.showwarning('No selection', 'Select an assignment from the list to update.')
			return

		ticket_val = self.ticket_combo.get()
		mechanic_val = self.mechanic_combo.get()
		hours_val = self.hours_entry.get()
		work_desc = self.work_desc_text.get('1.0', tk.END).strip()

		valid, msg = self.validate_inputs(ticket_val, mechanic_val, hours_val)
		if not valid:
			messagebox.showerror('Invalid input', msg)
			return

		try:
			ticket_id = int(ticket_val.split(' - ')[0])
			mechanic_id = int(mechanic_val.split(' - ')[0])
			hours = float(hours_val)
		except Exception:
			messagebox.showerror('Invalid selection', 'Could not parse ticket or mechanic ID.')
			return

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('UPDATE TicketAssignments SET ticket_id=?, mechanic_id=?, hours_worked=?, work_description=? WHERE assignment_id=?',
					(ticket_id, mechanic_id, hours, work_desc or None, self.editing_assignment_id))
			conn.commit()
			conn.close()
			messagebox.showinfo('Success', f'Assignment updated (id={self.editing_assignment_id}).')
			self.clear_form()
			self.load_assignments()
		except Exception as e:
			messagebox.showerror('Error', f'Failed to update assignment: {e}')

	def on_delete(self):
		sel = self.tree.selection()
		if not sel:
			messagebox.showwarning('No selection', 'Select an assignment from the list to delete.')
			return
		vals = self.tree.item(sel[0])['values']
		aid = vals[0]
		if not messagebox.askyesno('Confirm delete', f'Are you sure you want to delete assignment id {aid}?'):
			return
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('DELETE FROM TicketAssignments WHERE assignment_id = ?', (aid,))
			conn.commit()
			conn.close()
			messagebox.showinfo('Deleted', f'Assignment id {aid} deleted.')
			self.clear_form()
			self.load_assignments()
		except Exception as e:
			messagebox.showerror('Error', f'Failed to delete assignment: {e}')

	def sort_column(self, col, reverse):
		"""Sort treeview by column when heading is clicked."""
		items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
		try:
			# Try numeric sort for id, hours, labor_cost
			if col in ('id', 'hours'):
				items.sort(key=lambda t: float(str(t[0])) if str(t[0]) else 0, reverse=reverse)
			elif col == 'labor_cost':
				# Strip $ and convert to float
				items.sort(key=lambda t: float(str(t[0]).replace('$','').replace(',','')) if str(t[0]) and str(t[0]) != '$0.00' else 0, reverse=reverse)
			else:
				items.sort(key=lambda t: str(t[0]), reverse=reverse)
		except Exception:
			items.sort(reverse=reverse)

		# Rearrange items in sorted order
		for index, (val, k) in enumerate(items):
			self.tree.move(k, '', index)

		# Reverse sort next time
		self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

	def on_tree_double_click(self, event):
		"""Show full work description in a popup on double-click."""
		sel = self.tree.selection()
		if not sel:
			return
		vals = self.tree.item(sel[0])['values']
		if not vals or len(vals) < 6:
			return
		assignment_id = vals[0]
		
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT work_description FROM TicketAssignments WHERE assignment_id = ?', (assignment_id,))
			row = cur.fetchone()
			conn.close()
			if row:
				work_desc = row[0] or '(No work description)'
				# Create popup window
				popup = tk.Toplevel(self)
				popup.title(f'Work Description - Assignment #{assignment_id}')
				popup.geometry('600x400')
				
				text_widget = tk.Text(popup, wrap='word', font=('Segoe UI', 10))
				text_widget.pack(fill='both', expand=True, padx=10, pady=10)
				text_widget.insert('1.0', work_desc)
				text_widget.config(state='disabled')
				
				close_btn = tk.Button(popup, text='Close', command=popup.destroy, width=12)
				close_btn.pack(pady=(0, 10))
		except Exception as e:
			messagebox.showerror('Error', f'Failed to load work description: {e}')

	def apply_filter(self):
		"""Apply ticket filter to assignments list."""
		filter_val = self.filter_ticket_combo.get()
		if not filter_val or filter_val == 'All':
			self.load_assignments()
		else:
			try:
				ticket_id = int(filter_val.split(' - ')[0])
				self.load_assignments(filter_ticket_id=ticket_id)
			except Exception as e:
				self.message_label.config(text=f'Filter error: {e}')

	def clear_filter(self):
		"""Clear ticket filter and show all assignments."""
		self.filter_ticket_combo.set('All')
		self.load_assignments()

	def export_assignments_csv(self):
		"""Export current assignments (respecting ticket filter) to CSV at workspace root."""
		try:
			import csv, os
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			query = '''SELECT ta.assignment_id,
						 t.ticket_id,
						 t.status,
						 c.name as customer,
						 COALESCE(b.make,'') || ' ' || COALESCE(b.model,'') as boat,
						 m.name as mechanic,
						 m.hourly_rate,
						 ta.hours_worked,
						 ta.work_description
					FROM TicketAssignments ta
					JOIN Tickets t ON ta.ticket_id=t.ticket_id
					JOIN Mechanics m ON ta.mechanic_id=m.mechanic_id
					LEFT JOIN Customers c ON t.customer_id=c.customer_id
					LEFT JOIN Boats b ON t.boat_id=b.boat_id'''
			params = []
			filter_val = self.filter_ticket_combo.get() if hasattr(self, 'filter_ticket_combo') else 'All'
			if filter_val and filter_val != 'All':
				try:
					tid = int(str(filter_val).split(' - ')[0])
					query += ' WHERE t.ticket_id = ?'
					params.append(tid)
				except Exception:
					pass
			query += ' ORDER BY ta.assignment_id DESC'
			cur.execute(query, params)
			rows = cur.fetchall()
			conn.close()
			out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assignments_export.csv')
			with open(out_path, 'w', newline='', encoding='utf-8') as f:
				w = csv.writer(f)
				w.writerow(['AssignmentID','TicketID','Status','Customer','Boat','Mechanic','HourlyRate','HoursWorked','LaborCost','WorkDescription'])
				for r in rows:
					assignment_id, ticket_id, status, customer, boat, mechanic, rate, hours, work = r
					labor_cost = (hours or 0) * (rate or 0)
					w.writerow([assignment_id, ticket_id, status, customer or '', boat or '', mechanic or '', f"{rate:.2f}" if rate is not None else '', hours or 0, f"{labor_cost:.2f}", work or ''])
			messagebox.showinfo('Exported', f'Assignments exported to {out_path}')
		except Exception as e:
			messagebox.showerror('Export error', f'Failed to export assignments: {e}')
