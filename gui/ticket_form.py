import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from db.db_utils import get_db_path


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
		tk.Label(self, text="Create / Edit Tickets", font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, columnspan=4, pady=(0,8))

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

		# Export CSV
		export_btn = tk.Button(btn_filt_frame, text='Export CSV', command=self.export_tickets_csv, width=12)
		export_btn.pack(side='left', padx=(6,0))

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
		self.tree.bind('<Double-1>', self.on_ticket_double_click)

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

	def on_ticket_double_click(self, event):
		"""Open a detailed view for the selected ticket, including customer, boat, engine, work, and parts."""
		sel = self.tree.selection()
		if not sel:
			return
		vals = self.tree.item(sel[0])['values']
		if not vals:
			return
		ticket_id = vals[0]

		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			# Summary: ticket + customer + boat + engine
			cur.execute('''
				SELECT t.ticket_id, t.status, t.date_opened, t.date_closed, t.description,
				       c.customer_id, c.name, c.phone, c.email, c.address,
				       b.boat_id, b.make, b.model,
				       e.engine_id, e.type, e.make, e.model, e.hp, e.serial_number
				FROM Tickets t
				LEFT JOIN Customers c ON t.customer_id=c.customer_id
				LEFT JOIN Boats b ON t.boat_id=b.boat_id
				LEFT JOIN Engines e ON b.boat_id=e.boat_id
				WHERE t.ticket_id = ?
			''', (ticket_id,))
			summary = cur.fetchone()

			# Work assignments
			cur.execute('''
				SELECT ta.assignment_id, m.name, m.hourly_rate, ta.hours_worked, ta.work_description
				FROM TicketAssignments ta
				JOIN Mechanics m ON ta.mechanic_id=m.mechanic_id
				WHERE ta.ticket_id = ?
				ORDER BY ta.assignment_id
			''', (ticket_id,))
			work_rows = cur.fetchall()

			# Parts applied
			cur.execute('''
				SELECT tp.ticket_part_id, p.name AS part_name, tp.quantity_used, p.price AS unit_price
				FROM TicketParts tp
				JOIN Parts p ON tp.part_id = p.part_id
				WHERE tp.ticket_id = ?
				ORDER BY tp.ticket_part_id
			''', (ticket_id,))
			part_rows = cur.fetchall()

			conn.close()
		except Exception as e:
			messagebox.showerror('Error', f'Failed to load ticket details: {e}')
			return

		# Build popup UI
		popup = tk.Toplevel(self)
		popup.title(f'Ticket #{ticket_id} — Details')
		popup.geometry('900x700')
		popup.resizable(True, True)

		nb = ttk.Notebook(popup)
		nb.pack(fill='both', expand=True)

		# Summary tab
		summary_frame = tk.Frame(nb)
		nb.add(summary_frame, text='Summary')
		text = tk.Text(summary_frame, wrap='word')
		text.pack(fill='both', expand=True)

		def _fmt_phone(p):
			if not p:
				return ''
			d = ''.join(ch for ch in str(p) if ch.isdigit())
			return f'({d[0:3]}){d[3:6]}-{d[6:10]}' if len(d) == 10 else str(p)

		if summary:
			(tid, status, opened, closed, desc,
			 cid, cname, cphone, cemail, caddr,
			 bid, bmake, bmodel,
			 eid, etype, emake, emodel, ehp, eserial) = summary
			lines = [
				f'Ticket #{tid} — {status or ""}',
				f'Opened: {opened or ""}   Closed: {closed or ""}',
				'',
				'Customer:',
				f'  {cname or ""}',
				f'  Phone: {_fmt_phone(cphone)}',
				f'  Email: {cemail or ""}',
				f'  Address: {caddr or ""}',
				'',
				'Boat:',
				f'  {bmake or ""} {bmodel or ""}',
				'',
				'Engine:',
				f'  Type: {etype or ""}  Make/Model: {emake or ""} {emodel or ""}  HP: {ehp or ""}  Serial: {eserial or ""}',
				'',
				'Description:',
				f'{desc or ""}'
			]
			text.insert('1.0', '\n'.join(lines))
		text.config(state='disabled')

		# Work tab
		work_frame = tk.Frame(nb)
		nb.add(work_frame, text='Work')
		work_tree = ttk.Treeview(work_frame, columns=('assignment','mechanic','rate','hours','cost','desc'), show='headings')
		work_tree.heading('assignment', text='Assignment ID')
		work_tree.heading('mechanic', text='Mechanic')
		work_tree.heading('rate', text='Hourly Rate')
		work_tree.heading('hours', text='Hours')
		work_tree.heading('cost', text='Labor Cost')
		work_tree.heading('desc', text='Work Description')
		work_tree.column('assignment', width=110, anchor='center')
		work_tree.column('mechanic', width=160)
		work_tree.column('rate', width=100, anchor='e')
		work_tree.column('hours', width=80, anchor='center')
		work_tree.column('cost', width=110, anchor='e')
		work_tree.column('desc', width=360)
		work_tree.pack(fill='both', expand=True)
		for r in work_rows:
			aid, mname, rate, hours, wdesc = r
			cost = (hours or 0) * (rate or 0)
			work_tree.insert('', 'end', values=(aid, mname, f"${rate:.2f}" if rate is not None else '', hours or 0, f"${cost:.2f}", wdesc or ''))

		# Parts tab
		parts_frame = tk.Frame(nb)
		nb.add(parts_frame, text='Parts')
		parts_tree = ttk.Treeview(parts_frame, columns=('part_id','name','qty','price','ext'), show='headings')
		parts_tree.heading('part_id', text='Part ID')
		parts_tree.heading('name', text='Part Name')
		parts_tree.heading('qty', text='Qty')
		parts_tree.heading('price', text='Unit Price')
		parts_tree.heading('ext', text='Ext Price')
		parts_tree.column('part_id', width=90, anchor='center')
		parts_tree.column('name', width=240)
		parts_tree.column('qty', width=60, anchor='center')
		parts_tree.column('price', width=100, anchor='e')
		parts_tree.column('ext', width=110, anchor='e')
		parts_tree.pack(fill='both', expand=True)
		for r in part_rows:
			pid, pname, qty, unit = r
			ext = (qty or 0) * (unit or 0)
			parts_tree.insert('', 'end', values=(pid, pname or '', qty or 0, f"${unit:.2f}" if unit is not None else '', f"${ext:.2f}"))

		# Action buttons
		btns = tk.Frame(popup)
		btns.pack(fill='x', padx=10, pady=10)

		status_btn = tk.Button(btns, text='Change Status', width=14, command=lambda: self._change_ticket_status_dialog(ticket_id))
		status_btn.pack(side='left', padx=(0,8))

		add_part_btn = tk.Button(btns, text='Add Part', width=12, command=lambda: self._add_ticket_part_dialog(ticket_id))
		add_part_btn.pack(side='left', padx=(0,8))

		add_labor_btn = tk.Button(btns, text='Add Labor', width=12, command=lambda: self._add_ticket_labor_dialog(ticket_id))
		add_labor_btn.pack(side='left')

	def _refresh_after_edit(self):
		"""Refresh tickets list and keep filters intact."""
		try:
			self.load_tickets()
		except Exception:
			pass

	def _change_ticket_status_dialog(self, ticket_id: int):
		dlg = tk.Toplevel(self)
		dlg.title(f'Change Status — Ticket #{ticket_id}')
		dlg.geometry('320x140')
		dlg.resizable(False, False)
		tk.Label(dlg, text='New Status').pack(pady=(12,6))
		status_combo = ttk.Combobox(dlg, state='readonly', values=['Open','In Progress','Closed'], width=18)
		status_combo.pack()
		status_combo.set('Open')
		def save_status():
			new_status = status_combo.get()
			try:
				conn = sqlite3.connect(self.db_path)
				cur = conn.cursor()
				cur.execute('UPDATE Tickets SET status=? WHERE ticket_id=?', (new_status, ticket_id))
				conn.commit()
				conn.close()
				messagebox.showinfo('Updated', f'Ticket #{ticket_id} status set to {new_status}.')
				dlg.destroy()
				self._refresh_after_edit()
			except Exception as e:
				messagebox.showerror('Error', f'Failed to update status: {e}')
		btns2 = tk.Frame(dlg)
		btns2.pack(pady=10)
		tk.Button(btns2, text='Save', command=save_status, width=10).pack(side='left', padx=6)
		tk.Button(btns2, text='Cancel', command=dlg.destroy, width=10).pack(side='left')

	def _add_ticket_part_dialog(self, ticket_id: int):
		dlg = tk.Toplevel(self)
		dlg.title(f'Add Part — Ticket #{ticket_id}')
		dlg.geometry('420x220')
		dlg.resizable(False, False)
		frm = tk.Frame(dlg)
		frm.pack(padx=10, pady=10, fill='x')
		tk.Label(frm, text='Part').grid(row=0, column=0, sticky='e', padx=(0,6))
		part_combo = ttk.Combobox(frm, state='readonly', width=40)
		part_combo.grid(row=0, column=1, sticky='w')
		tk.Label(frm, text='Qty').grid(row=1, column=0, sticky='e', padx=(0,6))
		qty_entry = tk.Entry(frm, width=10)
		qty_entry.grid(row=1, column=1, sticky='w')
		# Load parts list
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT part_id, name, price FROM Parts ORDER BY name')
			parts = cur.fetchall()
			conn.close()
			part_combo['values'] = [f"{p[0]} - {p[1]} (${p[2]:.2f})" for p in parts]
			if parts:
				part_combo.current(0)
		except Exception:
			part_combo['values'] = []
		def save_part():
			try:
				val = part_combo.get()
				if not val:
					messagebox.showerror('Input', 'Select a part')
					return
				pid = int(str(val).split(' - ')[0])
				qty = int(qty_entry.get())
				conn = sqlite3.connect(self.db_path)
				cur = conn.cursor()
				cur.execute('INSERT INTO TicketParts (ticket_id, part_id, quantity_used) VALUES (?, ?, ?)', (ticket_id, pid, qty))
				conn.commit()
				conn.close()
				messagebox.showinfo('Added', f'Added part x{qty} to Ticket #{ticket_id}')
				dlg.destroy()
				self._refresh_after_edit()
			except Exception as e:
				messagebox.showerror('Error', f'Failed to add part: {e}')
		btns2 = tk.Frame(dlg)
		btns2.pack(pady=10)
		tk.Button(btns2, text='Save', command=save_part, width=10).pack(side='left', padx=6)
		tk.Button(btns2, text='Cancel', command=dlg.destroy, width=10).pack(side='left')

	def _add_ticket_labor_dialog(self, ticket_id: int):
		dlg = tk.Toplevel(self)
		dlg.title(f'Add Labor — Ticket #{ticket_id}')
		dlg.geometry('520x300')
		dlg.resizable(False, False)
		frm = tk.Frame(dlg)
		frm.pack(padx=10, pady=10, fill='x')
		tk.Label(frm, text='Mechanic').grid(row=0, column=0, sticky='e', padx=(0,6))
		mech_combo = ttk.Combobox(frm, state='readonly', width=40)
		mech_combo.grid(row=0, column=1, sticky='w')
		tk.Label(frm, text='Hours').grid(row=1, column=0, sticky='e', padx=(0,6))
		hours_entry = tk.Entry(frm, width=12)
		hours_entry.grid(row=1, column=1, sticky='w')
		tk.Label(frm, text='Work Description').grid(row=2, column=0, sticky='ne', padx=(0,6))
		work_text = tk.Text(frm, width=40, height=6)
		work_text.grid(row=2, column=1, sticky='w')
		# Load mechanics
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			cur.execute('SELECT mechanic_id, name, hourly_rate FROM Mechanics ORDER BY name')
			mechs = cur.fetchall()
			conn.close()
			mech_combo['values'] = [f"{m[0]} - {m[1]} (${m[2]:.2f}/hr)" for m in mechs]
			if mechs:
				mech_combo.current(0)
		except Exception:
			mech_combo['values'] = []
		def save_labor():
			try:
				val = mech_combo.get()
				if not val:
					messagebox.showerror('Input', 'Select a mechanic')
					return
				mid = int(str(val).split(' - ')[0])
				hours = float(hours_entry.get())
				work = work_text.get('1.0', tk.END).strip() or None
				conn = sqlite3.connect(self.db_path)
				cur = conn.cursor()
				cur.execute('INSERT INTO TicketAssignments (ticket_id, mechanic_id, hours_worked, work_description) VALUES (?, ?, ?, ?)', (ticket_id, mid, hours, work))
				conn.commit()
				conn.close()
				messagebox.showinfo('Added', f'Added labor {hours}h to Ticket #{ticket_id}')
				dlg.destroy()
				self._refresh_after_edit()
			except Exception as e:
				messagebox.showerror('Error', f'Failed to add labor: {e}')
		btns2 = tk.Frame(dlg)
		btns2.pack(pady=10)
		tk.Button(btns2, text='Save', command=save_labor, width=10).pack(side='left', padx=6)
		tk.Button(btns2, text='Cancel', command=dlg.destroy, width=10).pack(side='left')

	def export_tickets_csv(self):
		"""Export current tickets list to CSV at workspace root."""
		try:
			conn = sqlite3.connect(self.db_path)
			cur = conn.cursor()
			# Build query using same filters as apply_filters()
			query = '''SELECT t.ticket_id, t.status, c.name as customer, 
						COALESCE(b.make,'') || ' ' || COALESCE(b.model,'') as boat,
						t.date_opened, t.date_closed, t.description
					FROM Tickets t
					LEFT JOIN Customers c ON t.customer_id=c.customer_id
					LEFT JOIN Boats b ON t.boat_id=b.boat_id'''
			params = []
			where = []
			status = self.status_filter.get()
			if status and status != 'All':
				where.append('t.status = ?')
				params.append(status)
			cust_txt = self.customer_filter_entry.get().strip() if hasattr(self, 'customer_filter_entry') else ''
			if cust_txt:
				where.append('c.name LIKE ?')
				params.append(f'%{cust_txt}%')
			boat_txt = self.boat_filter_entry.get().strip() if hasattr(self, 'boat_filter_entry') else ''
			if boat_txt:
				where.append("(b.make || ' ' || b.model) LIKE ?")
				params.append(f'%{boat_txt}%')
			opened_from = self.opened_from_entry.get().strip() if hasattr(self, 'opened_from_entry') else ''
			if opened_from:
				where.append('t.date_opened >= ?')
				params.append(opened_from)
			opened_to = self.opened_to_entry.get().strip() if hasattr(self, 'opened_to_entry') else ''
			if opened_to:
				where.append('t.date_opened <= ?')
				params.append(opened_to)
			closed_from = self.closed_from_entry.get().strip() if hasattr(self, 'closed_from_entry') else ''
			if closed_from:
				where.append('t.date_closed >= ?')
				params.append(closed_from)
			closed_to = self.closed_to_entry.get().strip() if hasattr(self, 'closed_to_entry') else ''
			if closed_to:
				where.append('t.date_closed <= ?')
				params.append(closed_to)
			if where:
				query += ' WHERE ' + ' AND '.join(where)
			query += ' ORDER BY t.ticket_id'
			cur.execute(query, params)
			rows = cur.fetchall()
			conn.close()
			# Write CSV
			import csv, os
			out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tickets_export.csv')
			with open(out_path, 'w', newline='', encoding='utf-8') as f:
				w = csv.writer(f)
				w.writerow(['ID','Status','Customer','Boat','Opened','Closed','Description'])
				for r in rows:
					w.writerow(r)
			messagebox.showinfo('Exported', f'Tickets exported to {out_path}')
		except Exception as e:
			messagebox.showerror('Export error', f'Failed to export tickets: {e}')

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
