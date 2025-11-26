import tkinter as tk
from tkinter import ttk
from gui.customer_form import CustomerForm
from gui.boat_form import BoatForm
from gui.engine_form import EngineForm
from gui.ticket_form import TicketForm
from gui.mechanic_form import MechanicForm
from gui.ticket_assignment_form import TicketAssignmentForm
from db.db_utils import get_db_path, ensure_engine_columns, ensure_assignment_work_description


def main():
	root = tk.Tk()
	root.title("Cajun Shop — Create Customer / Boat")

	# Notebook with tabs for Customer and Boat
	notebook = ttk.Notebook(root)
	notebook.pack(padx=12, pady=12, fill='both', expand=True)

	cust_frame = CustomerForm(notebook)
	notebook.add(cust_frame, text='Customers')

	# add boats tab
	boat_frame = BoatForm(notebook)
	notebook.add(boat_frame, text='Boats')

	# ensure DB schema compatibility (add engine cols if missing) before creating forms
	try:
		ensure_engine_columns(get_db_path())
		ensure_assignment_work_description(get_db_path())
	except Exception:
		# best-effort; continue even if migration helper fails
		pass

	engine_frame = EngineForm(notebook)
	notebook.add(engine_frame, text='Engines')

	# Tickets tab
	ticket_frame = TicketForm(notebook)
	notebook.add(ticket_frame, text='Tickets')

	# Mechanics tab
	mechanic_tab = MechanicForm(notebook, db_path=get_db_path())
	notebook.add(mechanic_tab, text="Mechanics")

	# Ticket Assignments tab
	assignment_tab = TicketAssignmentForm(notebook, db_path=get_db_path())
	notebook.add(assignment_tab, text="Assignments")

	# Auto-refresh wiring: when a create/update/delete happens in one form, refresh relevant lists in others
	# Customer changes -> reload Boat customer selector and Engine boat lists
	cust_frame.add_change_listener(lambda: (boat_frame.load_customers(), engine_frame.load_boats(), ticket_frame.load_customers(), ticket_frame.load_tickets()))

	# Boat changes -> reload Engine boat selector and engine list
	boat_frame.add_change_listener(lambda: (engine_frame.load_boats(), engine_frame.load_engines(), ticket_frame.load_boats(), ticket_frame.load_tickets()))

	# Ticket changes -> reload assignments ticket list
	ticket_frame.add_change_listener(lambda: assignment_tab.load_tickets())

	# Mechanic changes -> reload assignments mechanic list (if we add listeners to mechanic_tab in future)
	# Note: MechanicForm doesn't have add_change_listener yet, but we can add it if needed
	# Allow resizing so larger forms (like Assignments) are visible
	root.resizable(True, True)
	root.mainloop()


if __name__ == '__main__':
	main()



