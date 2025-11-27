import tkinter as tk
from tkinter import ttk, font
from gui.customer_form import CustomerForm
from gui.boat_form import BoatForm
from gui.engine_form import EngineForm
from gui.ticket_form import TicketForm
from gui.mechanic_form import MechanicForm
from gui.ticket_assignment_form import TicketAssignmentForm
from db.db_utils import get_db_path, ensure_database_exists


def open_customers_window(root):
	"""Open Customers management window."""
	win = tk.Toplevel(root)
	win.title("Cajun Marine — Customers")
	win.geometry("900x600")
	win.resizable(True, True)
	
	cust_frame = CustomerForm(win)
	cust_frame.pack(padx=12, pady=12, fill='both', expand=True)


def open_tickets_window(root):
	"""Open Tickets management window."""
	win = tk.Toplevel(root)
	win.title("Cajun Marine — Tickets")
	win.geometry("1000x700")
	win.resizable(True, True)
	
	ticket_frame = TicketForm(win)
	ticket_frame.pack(padx=12, pady=12, fill='both', expand=True)


def open_admin_window(root):
	"""Open Admin window with all management tabs."""
	win = tk.Toplevel(root)
	win.title("Cajun Marine — Admin")
	win.geometry("1100x750")
	win.resizable(True, True)

	notebook = ttk.Notebook(win)
	notebook.pack(padx=12, pady=12, fill='both', expand=True)

	cust_frame = CustomerForm(notebook)
	notebook.add(cust_frame, text='Customers')

	boat_frame = BoatForm(notebook)
	notebook.add(boat_frame, text='Boats')

	engine_frame = EngineForm(notebook)
	notebook.add(engine_frame, text='Engines')

	ticket_frame = TicketForm(notebook)
	notebook.add(ticket_frame, text='Tickets')

	mechanic_tab = MechanicForm(notebook, db_path=get_db_path())
	notebook.add(mechanic_tab, text="Mechanics")

	assignment_tab = TicketAssignmentForm(notebook, db_path=get_db_path())
	notebook.add(assignment_tab, text="Assignments")

	# Auto-refresh wiring
	cust_frame.add_change_listener(lambda: (boat_frame.load_customers(), engine_frame.load_boats(), ticket_frame.load_customers(), ticket_frame.load_tickets()))
	boat_frame.add_change_listener(lambda: (engine_frame.load_boats(), engine_frame.load_engines(), ticket_frame.load_boats(), ticket_frame.load_tickets()))
	ticket_frame.add_change_listener(lambda: assignment_tab.load_tickets())


def main():
	root = tk.Tk()
	root.title("Cajun Marine")
	root.geometry("800x600")
	root.resizable(False, False)
	root.configure(bg='#1a3a52')

	# Ensure database exists
	ensure_database_exists()

	# Main container
	main_frame = tk.Frame(root, bg='#1a3a52')
	main_frame.pack(fill='both', expand=True, padx=40, pady=40)

	# Welcome header
	title_font = font.Font(family='Arial', size=42, weight='bold')
	title = tk.Label(
		main_frame,
		text="Welcome to Cajun Marine",
		font=title_font,
		fg='white',
		bg='#1a3a52',
		wraplength=760,
		justify='center'
	)
	title.pack(pady=(20, 40), fill='x')

	# Placeholder for future image
	image_placeholder = tk.Label(main_frame, text="[Company Logo Here]", font=('Arial', 12, 'italic'), 
								  fg='#a0c4e0', bg='#1a3a52', width=30, height=3, relief='flat')
	image_placeholder.pack(pady=(0, 40))

	# Button frame
	btn_frame = tk.Frame(main_frame, bg='#1a3a52')
	btn_frame.pack(pady=20)

	# Navigation buttons
	btn_style = {
		'font': ('Arial', 16, 'bold'),
		'width': 18,
		'height': 2,
		'bg': '#2d6a9f',
		'fg': 'white',
		'activebackground': '#3d7aaf',
		'activeforeground': 'white',
		'relief': 'raised',
		'bd': 3,
		'cursor': 'hand2'
	}

	customers_btn = tk.Button(btn_frame, text="CUSTOMERS", command=lambda: open_customers_window(root), **btn_style)
	customers_btn.pack(pady=10)

	tickets_btn = tk.Button(btn_frame, text="TICKETS", command=lambda: open_tickets_window(root), **btn_style)
	tickets_btn.pack(pady=10)

	admin_btn = tk.Button(btn_frame, text="ADMIN", command=lambda: open_admin_window(root), **btn_style)
	admin_btn.pack(pady=10)

	root.mainloop()


if __name__ == '__main__':
	main()



