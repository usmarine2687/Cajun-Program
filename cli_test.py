"""
Cajun Marine CLI Test Harness
Interactive command-line interface for testing business logic.
"""
import sys
from datetime import datetime
from db import service


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_dict(data, indent=0):
    """Pretty print dictionary."""
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, list):
            print(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    print_dict(item, indent + 1)
                else:
                    print(f"{prefix}  - {item}")
        elif isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_dict(value, indent + 1)
        else:
            print(f"{prefix}{key}: {value}")


# ============================================================================
# CUSTOMER MANAGEMENT
# ============================================================================

def customer_menu():
    """Customer management menu."""
    while True:
        print_header("Customer Management")
        print("1. Create customer")
        print("2. View customer")
        print("3. List all customers")
        print("4. Update customer")
        print("0. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            create_customer_interactive()
        elif choice == '2':
            view_customer_interactive()
        elif choice == '3':
            list_customers_interactive()
        elif choice == '4':
            update_customer_interactive()
        elif choice == '0':
            break


def create_customer_interactive():
    """Create customer interactively."""
    print("\n--- Create Customer ---")
    name = input("Name: ").strip()
    phone = input("Phone (optional): ").strip() or None
    email = input("Email (optional): ").strip() or None
    address = input("Address (optional): ").strip() or None
    
    tax_exempt = input("Tax exempt? (y/n): ").strip().lower() == 'y'
    tax_exempt_certificate = None
    if tax_exempt:
        tax_exempt_certificate = input("Certificate number: ").strip() or None
    
    out_of_state = input("Out of state? (y/n): ").strip().lower() == 'y'
    
    try:
        customer_id = service.create_customer(
            name, phone, email, address, 
            int(tax_exempt), tax_exempt_certificate, int(out_of_state)
        )
        print(f"\n✓ Customer created with ID: {customer_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_customer_interactive():
    """View customer by ID."""
    customer_id = input("\nCustomer ID: ").strip()
    try:
        customer = service.get_customer(int(customer_id))
        if customer:
            print("\n--- Customer Details ---")
            print_dict(customer)
        else:
            print("\n✗ Customer not found")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def list_customers_interactive():
    """List all customers."""
    try:
        customers = service.list_customers()
        print(f"\n--- All Customers ({len(customers)}) ---")
        for c in customers:
            tax_status = " [TAX EXEMPT]" if c.get('tax_exempt') else ""
            out_of_state_status = " [OUT OF STATE]" if c.get('out_of_state') else ""
            print(f"{c['customer_id']:3d}. {c['name']:<30s} {c.get('phone', ''):<15s}{tax_status}{out_of_state_status}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def update_customer_interactive():
    """Update customer."""
    customer_id = input("\nCustomer ID: ").strip()
    try:
        customer = service.get_customer(int(customer_id))
        if not customer:
            print("\n✗ Customer not found")
            return
        
        print("\n--- Current Details ---")
        print_dict(customer)
        
        print("\n--- Update (press Enter to skip) ---")
        updates = {}
        
        name = input(f"Name [{customer['name']}]: ").strip()
        if name:
            updates['name'] = name
        
        phone = input(f"Phone [{customer.get('phone', '')}]: ").strip()
        if phone:
            updates['phone'] = phone
        
        if updates:
            success = service.update_customer(int(customer_id), **updates)
            if success:
                print("\n✓ Customer updated")
            else:
                print("\n✗ Update failed")
        else:
            print("\n✗ No changes made")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# PARTS MANAGEMENT
# ============================================================================

def parts_menu():
    """Parts management menu."""
    while True:
        print_header("Parts Management")
        print("1. Create part")
        print("2. View part")
        print("3. List all parts")
        print("0. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            create_part_interactive()
        elif choice == '2':
            view_part_interactive()
        elif choice == '3':
            list_parts_interactive()
        elif choice == '0':
            break


def create_part_interactive():
    """Create part interactively."""
    print("\n--- Create Part ---")
    part_number = input("Part number (optional): ").strip() or None
    name = input("Part name: ").strip()
    
    try:
        stock_quantity = int(input("Stock quantity (default 0): ").strip() or '0')
        price = float(input("Price (default 0.00): ").strip() or '0')
        
        supplier_name = input("Supplier name (optional): ").strip() or None
        cost_input = input("Cost from supplier (optional): ").strip()
        cost_from_supplier = float(cost_input) if cost_input else None
        
        retail_input = input("Retail price (optional): ").strip()
        retail_price = float(retail_input) if retail_input else None
        
        taxable = input("Taxable? (y/n, default y): ").strip().lower() != 'n'
        
        part_id = service.create_part(
            part_number, name, stock_quantity, price,
            supplier_name, cost_from_supplier, retail_price, int(taxable)
        )
        print(f"\n✓ Part created with ID: {part_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_part_interactive():
    """View part by ID."""
    part_id = input("\nPart ID: ").strip()
    try:
        part = service.get_part(int(part_id))
        if part:
            print("\n--- Part Details ---")
            print_dict(part)
        else:
            print("\n✗ Part not found")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def list_parts_interactive():
    """List all parts."""
    try:
        parts = service.list_parts()
        print(f"\n--- All Parts ({len(parts)}) ---")
        for p in parts:
            taxable = "[TAXABLE]" if p.get('taxable') else "[NON-TAXABLE]"
            print(f"{p['part_id']:3d}. {p['name']:<30s} ${p['price']:>7.2f} (Stock: {p['stock_quantity']:>3d}) {taxable}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# NEW ENGINE MANAGEMENT
# ============================================================================

def new_engines_menu():
    """New engines management menu."""
    while True:
        print_header("New Engine Inventory")
        print("1. Add new engine to inventory")
        print("2. View engine details")
        print("3. List all engines")
        print("4. Sell engine to customer")
        print("5. Mark engine as registered with Tohatsu")
        print("6. Check engines needing registration")
        print("0. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            add_new_engine_interactive()
        elif choice == '2':
            view_new_engine_interactive()
        elif choice == '3':
            list_new_engines_interactive()
        elif choice == '4':
            sell_engine_interactive()
        elif choice == '5':
            mark_engine_registered_interactive()
        elif choice == '6':
            check_registration_needed_interactive()
        elif choice == '0':
            break


def add_new_engine_interactive():
    """Add new engine to inventory."""
    print("\n--- Add New Tohatsu Engine ---")
    try:
        hp = int(input("HP: ").strip())
        model = input("Model: ").strip()
        serial_number = input("Serial number: ").strip()
        
        purchase_input = input("Purchase price (optional): ").strip()
        purchase_price = float(purchase_input) if purchase_input else None
        
        notes = input("Notes (optional): ").strip() or None
        
        engine_id = service.create_new_engine(hp, model, serial_number, purchase_price, notes)
        print(f"\n✓ Engine added to inventory with ID: {engine_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_new_engine_interactive():
    """View engine details."""
    engine_id = input("\nEngine ID: ").strip()
    try:
        engine = service.get_new_engine(int(engine_id))
        if engine:
            print("\n--- Engine Details ---")
            print_dict(engine)
            
            # Check if needs registration
            if (engine.get('status') == 'Sold' and 
                engine.get('paid_in_full') == 1 and 
                engine.get('date_installed') and
                engine.get('registered_with_tohatsu') == 0):
                
                from datetime import datetime, timedelta
                install_date = datetime.strptime(engine['date_installed'], '%Y-%m-%d')
                days_since_install = (datetime.now() - install_date).days
                
                if days_since_install > 30:
                    print("\n⚠️  WARNING: Engine needs Tohatsu registration!")
                    print(f"    Installed {days_since_install} days ago")
        else:
            print("\n✗ Engine not found")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def list_new_engines_interactive():
    """List all engines."""
    print("\n1. All engines")
    print("2. In Stock only")
    print("3. Sold only")
    choice = input("Choice: ").strip()
    
    status_filter = None
    if choice == '2':
        status_filter = 'In Stock'
    elif choice == '3':
        status_filter = 'Sold'
    
    try:
        engines = service.list_new_engines(status_filter)
        title = f"All Engines ({len(engines)})" if not status_filter else f"{status_filter} Engines ({len(engines)})"
        print(f"\n--- {title} ---")
        for e in engines:
            status = f"[{e['status']}]"
            registered = " ✓ Registered" if e.get('registered_with_tohatsu') else ""
            print(f"{e['new_engine_id']:3d}. {e['hp']}HP {e['model']:<20s} SN: {e['serial_number']} {status}{registered}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def sell_engine_interactive():
    """Sell engine to customer."""
    print("\n--- Sell Engine ---")
    try:
        engine_id = int(input("Engine ID: ").strip())
        customer_id = int(input("Customer ID: ").strip())
        
        boat_input = input("Boat ID (optional): ").strip()
        boat_id = int(boat_input) if boat_input else None
        
        sale_price = float(input("Sale price: ").strip())
        
        date_sold = input("Date sold (YYYY-MM-DD, default today): ").strip()
        if not date_sold:
            date_sold = datetime.now().strftime('%Y-%m-%d')
        
        date_installed = input("Date installed (YYYY-MM-DD, optional): ").strip() or None
        
        paid_in_full = input("Paid in full? (y/n): ").strip().lower() == 'y'
        
        success = service.sell_new_engine(
            engine_id, customer_id, boat_id, sale_price, 
            date_sold, date_installed, int(paid_in_full)
        )
        
        if success:
            print("\n✓ Engine sold")
        else:
            print("\n✗ Sale failed (engine may not be in stock)")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def mark_engine_registered_interactive():
    """Mark engine as registered with Tohatsu."""
    engine_id = input("\nEngine ID: ").strip()
    try:
        registration_date = datetime.now().strftime('%Y-%m-%d')
        success = service.update_new_engine(
            int(engine_id),
            registered_with_tohatsu=1,
            registration_date=registration_date
        )
        if success:
            print(f"\n✓ Engine marked as registered on {registration_date}")
        else:
            print("\n✗ Update failed")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def check_registration_needed_interactive():
    """Check engines needing registration."""
    try:
        engines = service.get_engines_needing_registration()
        if engines:
            print(f"\n⚠️  {len(engines)} ENGINE(S) NEED REGISTRATION")
            print("-" * 80)
            for e in engines:
                from datetime import datetime
                install_date = datetime.strptime(e['date_installed'], '%Y-%m-%d')
                days_overdue = (datetime.now() - install_date).days - 30
                print(f"\nEngine ID: {e['new_engine_id']}")
                print(f"  {e['hp']}HP {e['model']} - SN: {e['serial_number']}")
                print(f"  Customer: {e.get('customer_name', 'N/A')} - {e.get('customer_phone', 'N/A')}")
                print(f"  Installed: {e['date_installed']} ({days_overdue} days overdue)")
        else:
            print("\n✓ No engines need registration")
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# ESTIMATE MANAGEMENT
# ============================================================================

def estimates_menu():
    """Estimates management menu."""
    while True:
        print_header("Estimate Management")
        print("1. Create estimate")
        print("2. Add line item to estimate")
        print("3. View estimate with totals")
        print("4. List all estimates")
        print("0. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            create_estimate_interactive()
        elif choice == '2':
            add_estimate_line_item_interactive()
        elif choice == '3':
            view_estimate_interactive()
        elif choice == '4':
            list_estimates_interactive()
        elif choice == '0':
            break


def create_estimate_interactive():
    """Create estimate."""
    print("\n--- Create Estimate ---")
    try:
        customer_id = int(input("Customer ID: ").strip())
        
        boat_input = input("Boat ID (optional): ").strip()
        boat_id = int(boat_input) if boat_input else None
        
        engine_input = input("Engine ID (optional): ").strip()
        engine_id = int(engine_input) if engine_input else None
        
        insurance_company = input("Insurance company (optional): ").strip() or None
        claim_number = input("Claim number (optional): ").strip() or None
        notes = input("Notes (optional): ").strip() or None
        
        estimate_id = service.create_estimate(
            customer_id, boat_id, engine_id,
            insurance_company, claim_number, notes
        )
        print(f"\n✓ Estimate created with ID: {estimate_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def add_estimate_line_item_interactive():
    """Add line item to estimate."""
    print("\n--- Add Line Item ---")
    try:
        estimate_id = int(input("Estimate ID: ").strip())
        
        print("\nItem type:")
        print("1. Part")
        print("2. Labor")
        choice = input("Choice: ").strip()
        item_type = 'part' if choice == '1' else 'labor'
        
        description = input("Description: ").strip()
        quantity = float(input("Quantity (default 1.0): ").strip() or '1.0')
        unit_price = float(input("Unit price: ").strip())
        
        line_item_id = service.add_estimate_line_item(
            estimate_id, item_type, description, quantity, unit_price
        )
        print(f"\n✓ Line item added with ID: {line_item_id}")
        
        # Recalculate totals
        print("\nRecalculating totals...")
        subtotal, tax, total = service.calculate_estimate_totals(estimate_id)
        print(f"  Subtotal: ${subtotal:.2f}")
        print(f"  Tax:      ${tax:.2f}")
        print(f"  Total:    ${total:.2f}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_estimate_interactive():
    """View estimate with totals."""
    estimate_id = input("\nEstimate ID: ").strip()
    try:
        estimate = service.get_estimate_details(int(estimate_id))
        if estimate:
            print("\n--- Estimate Details ---")
            print(f"Estimate ID: {estimate['estimate_id']}")
            print(f"Customer: {estimate.get('customer_name')} ({estimate.get('customer_phone', 'N/A')})")
            print(f"Date: {estimate['date_created']}")
            if estimate.get('insurance_company'):
                print(f"Insurance: {estimate['insurance_company']} - Claim #{estimate.get('claim_number', 'N/A')}")
            
            print("\nLine Items:")
            for item in estimate.get('line_items', []):
                print(f"  [{item['item_type'].upper()}] {item['description']}")
                print(f"    {item['quantity']} x ${item['unit_price']:.2f} = ${item['line_total']:.2f}")
            
            print(f"\nSubtotal: ${estimate['subtotal']:.2f}")
            print(f"Tax:      ${estimate['tax_amount']:.2f}")
            print(f"TOTAL:    ${estimate['total']:.2f}")
        else:
            print("\n✗ Estimate not found")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def list_estimates_interactive():
    """List all estimates."""
    try:
        estimates = service.list_estimates()
        print(f"\n--- All Estimates ({len(estimates)}) ---")
        for e in estimates:
            print(f"{e['estimate_id']:3d}. {e['date_created']} - {e.get('customer_name', 'N/A'):<30s} ${e.get('total', 0):.2f}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# TICKET MANAGEMENT
# ============================================================================

def tickets_menu():
    """Tickets management menu."""
    while True:
        print_header("Ticket Management")
        print("1. Create ticket")
        print("2. Add part to ticket")
        print("3. Add labor to ticket")
        print("4. Update ticket status")
        print("5. View ticket details")
        print("6. Calculate ticket totals")
        print("7. List all tickets")
        print("0. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            create_ticket_interactive()
        elif choice == '2':
            add_ticket_part_interactive()
        elif choice == '3':
            add_ticket_labor_interactive()
        elif choice == '4':
            update_ticket_status_interactive()
        elif choice == '5':
            view_ticket_interactive()
        elif choice == '6':
            calculate_ticket_totals_interactive()
        elif choice == '7':
            list_tickets_interactive()
        elif choice == '0':
            break


def create_ticket_interactive():
    """Create ticket."""
    print("\n--- Create Ticket ---")
    try:
        customer_id = int(input("Customer ID: ").strip())
        boat_id = int(input("Boat ID: ").strip())
        
        engine_input = input("Engine ID (optional): ").strip()
        engine_id = int(engine_input) if engine_input else None
        
        description = input("Description: ").strip() or None
        
        ticket_id = service.create_ticket(customer_id, boat_id, engine_id, description)
        print(f"\n✓ Ticket created with ID: {ticket_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def add_ticket_part_interactive():
    """Add part to ticket."""
    print("\n--- Add Part to Ticket ---")
    try:
        ticket_id = int(input("Ticket ID: ").strip())
        part_id = int(input("Part ID: ").strip())
        quantity = int(input("Quantity: ").strip())
        
        ticket_part_id = service.add_ticket_part(ticket_id, part_id, quantity)
        print(f"\n✓ Part added with ID: {ticket_part_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def add_ticket_labor_interactive():
    """Add labor to ticket."""
    print("\n--- Add Labor to Ticket ---")
    try:
        ticket_id = int(input("Ticket ID: ").strip())
        mechanic_id = int(input("Mechanic ID: ").strip())
        hours = float(input("Hours worked: ").strip())
        work_description = input("Work description (optional): ").strip() or None
        
        labor_input = input("Labor rate (optional, uses mechanic's rate if blank): ").strip()
        labor_rate = float(labor_input) if labor_input else None
        
        assignment_id = service.add_ticket_labor(
            ticket_id, mechanic_id, hours, work_description, labor_rate
        )
        print(f"\n✓ Labor added with ID: {assignment_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def update_ticket_status_interactive():
    """Update ticket status."""
    print("\n--- Update Ticket Status ---")
    print("Statuses: Open, Working, Awaiting Parts, Awaiting Customer,")
    print("          Awaiting Payment, Awaiting Pickup, Closed")
    
    try:
        ticket_id = int(input("\nTicket ID: ").strip())
        new_status = input("New status: ").strip()
        
        success = service.update_ticket_status(ticket_id, new_status)
        if success:
            print(f"\n✓ Ticket status updated to '{new_status}'")
        else:
            print("\n✗ Update failed")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_ticket_interactive():
    """View ticket details."""
    ticket_id = input("\nTicket ID: ").strip()
    try:
        ticket = service.get_ticket_details(int(ticket_id))
        if ticket:
            print("\n--- Ticket Details ---")
            print(f"Ticket ID: {ticket['ticket_id']}")
            print(f"Customer: {ticket.get('customer_name')} ({ticket.get('customer_phone', 'N/A')})")
            print(f"Boat: {ticket.get('boat_make', 'N/A')} {ticket.get('boat_model', 'N/A')}")
            print(f"Status: {ticket['status']}")
            print(f"Opened: {ticket['date_opened']}")
            if ticket.get('description'):
                print(f"Description: {ticket['description']}")
            
            print("\nParts:")
            for part in ticket.get('parts', []):
                print(f"  {part['part_name']} - Qty: {part['quantity_used']} x ${part['price']:.2f}")
            
            print("\nLabor:")
            for labor in ticket.get('labor', []):
                print(f"  {labor['mechanic_name']} - {labor['hours_worked']} hrs @ ${labor['labor_rate']:.2f}/hr")
                if labor.get('work_description'):
                    print(f"    Description: {labor['work_description']}")
            
            if ticket.get('total'):
                print(f"\nSubtotal: ${ticket.get('subtotal', 0):.2f}")
                print(f"Tax:      ${ticket.get('tax_amount', 0):.2f}")
                print(f"TOTAL:    ${ticket['total']:.2f}")
        else:
            print("\n✗ Ticket not found")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def calculate_ticket_totals_interactive():
    """Calculate ticket totals."""
    print("\n--- Calculate Ticket Totals ---")
    try:
        ticket_id = int(input("Ticket ID: ").strip())
        
        payment_method = input("Payment method (optional): ").strip() or None
        
        engine_input = input("New engine ID if sold (optional): ").strip()
        new_engine_id = int(engine_input) if engine_input else None
        
        subtotal, tax, total = service.calculate_ticket_totals(
            ticket_id, payment_method, new_engine_id
        )
        
        print(f"\n✓ Totals calculated:")
        print(f"  Subtotal: ${subtotal:.2f}")
        print(f"  Tax:      ${tax:.2f}")
        print(f"  Total:    ${total:.2f}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def list_tickets_interactive():
    """List tickets."""
    print("\n1. All tickets")
    print("2. Filter by status")
    choice = input("Choice: ").strip()
    
    status_filter = None
    if choice == '2':
        status_filter = input("Status: ").strip()
    
    try:
        tickets = service.list_tickets(status_filter)
        title = f"All Tickets ({len(tickets)})" if not status_filter else f"{status_filter} Tickets ({len(tickets)})"
        print(f"\n--- {title} ---")
        for t in tickets:
            print(f"{t['ticket_id']:3d}. [{t['status']:<20s}] {t['date_opened']} - {t.get('customer_name', 'N/A')}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# DEPOSIT MANAGEMENT
# ============================================================================

def deposits_menu():
    """Deposits management menu."""
    while True:
        print_header("Deposit Management")
        print("1. Add deposit to ticket")
        print("2. View ticket deposits")
        print("3. Check balance due")
        print("0. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            add_deposit_interactive()
        elif choice == '2':
            view_deposits_interactive()
        elif choice == '3':
            check_balance_interactive()
        elif choice == '0':
            break


def add_deposit_interactive():
    """Add deposit to ticket."""
    print("\n--- Add Deposit ---")
    try:
        ticket_id = int(input("Ticket ID: ").strip())
        amount = float(input("Amount: ").strip())
        payment_method = input("Payment method (optional): ").strip() or None
        notes = input("Notes (optional): ").strip() or None
        
        deposit_id = service.add_deposit(ticket_id, amount, payment_method, notes)
        print(f"\n✓ Deposit added with ID: {deposit_id}")
        
        # Show balance
        balance = service.calculate_balance_due(ticket_id)
        print(f"  Balance due: ${balance:.2f}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def view_deposits_interactive():
    """View ticket deposits."""
    ticket_id = input("\nTicket ID: ").strip()
    try:
        deposits = service.get_ticket_deposits(int(ticket_id))
        if deposits:
            print(f"\n--- Deposits for Ticket #{ticket_id} ---")
            total_paid = 0.0
            for d in deposits:
                print(f"{d['payment_date']}: ${d['amount']:.2f} ({d.get('payment_method', 'N/A')})")
                if d.get('notes'):
                    print(f"  Notes: {d['notes']}")
                total_paid += d['amount']
            print(f"\nTotal paid: ${total_paid:.2f}")
        else:
            print("\n✗ No deposits found")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def check_balance_interactive():
    """Check balance due."""
    ticket_id = input("\nTicket ID: ").strip()
    try:
        balance = service.calculate_balance_due(int(ticket_id))
        print(f"\nBalance due: ${balance:.2f}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# TAX CALCULATION TESTING
# ============================================================================

def tax_testing_menu():
    """Tax calculation testing menu."""
    while True:
        print_header("Tax Calculation Testing")
        print("1. Test tax-exempt customer scenario")
        print("2. Test out-of-state engine scenario")
        print("3. Test cash payment scenario")
        print("4. Test standard taxable scenario")
        print("0. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            test_tax_exempt_scenario()
        elif choice == '2':
            test_out_of_state_scenario()
        elif choice == '3':
            test_cash_payment_scenario()
        elif choice == '4':
            test_standard_scenario()
        elif choice == '0':
            break


def test_tax_exempt_scenario():
    """Test tax-exempt customer."""
    print("\n--- Tax-Exempt Customer Test ---")
    print("This scenario tests a business customer with tax-exempt certificate.")
    print("Expected: 0% tax on all items\n")
    
    try:
        # Create tax-exempt customer
        customer_id = service.create_customer(
            "Tax Exempt Business LLC",
            "555-1234",
            tax_exempt=1,
            tax_exempt_certificate="TX123456"
        )
        print(f"Created tax-exempt customer (ID: {customer_id})")
        
        # Create some line items
        line_items = [
            {'amount': 100.00, 'taxable': 1},  # $100 in taxable parts
            {'amount': 50.00, 'taxable': 1},   # $50 in labor
        ]
        
        subtotal, tax, total = service.calculate_tax(customer_id, line_items)
        
        print(f"\nLine items: ${sum(item['amount'] for item in line_items):.2f}")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Tax:      ${tax:.2f}")
        print(f"Total:    ${total:.2f}")
        
        if tax == 0.0:
            print("\n✓ TEST PASSED: Tax is $0.00")
        else:
            print(f"\n✗ TEST FAILED: Expected $0.00 tax, got ${tax:.2f}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_out_of_state_scenario():
    """Test out-of-state customer buying new engine."""
    print("\n--- Out-of-State Engine Purchase Test ---")
    print("This scenario tests an out-of-state customer buying a new engine.")
    print("Expected: 0% tax on new engine, 9.75% tax on other items\n")
    
    try:
        # Create out-of-state customer
        customer_id = service.create_customer(
            "Out of State Customer",
            "555-5678",
            out_of_state=1
        )
        print(f"Created out-of-state customer (ID: {customer_id})")
        
        # Line items (parts/labor)
        line_items = [
            {'amount': 50.00, 'taxable': 1},  # $50 in taxable parts
        ]
        
        new_engine_sale_price = 5000.00  # $5000 new engine
        
        subtotal, tax, total = service.calculate_tax(
            customer_id, line_items, 
            new_engine_sale_price=new_engine_sale_price
        )
        
        expected_tax = 50.00 * 0.0975  # Only parts are taxed
        
        print(f"\nNew engine: ${new_engine_sale_price:.2f}")
        print(f"Other items: ${sum(item['amount'] for item in line_items):.2f}")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Tax:      ${tax:.2f} (expected: ${expected_tax:.2f})")
        print(f"Total:    ${total:.2f}")
        
        if abs(tax - expected_tax) < 0.01:
            print("\n✓ TEST PASSED: Only non-engine items are taxed")
        else:
            print(f"\n✗ TEST FAILED: Expected ${expected_tax:.2f} tax, got ${tax:.2f}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_cash_payment_scenario():
    """Test cash payment with mixed taxable/non-taxable parts."""
    print("\n--- Cash Payment Test ---")
    print("This scenario tests cash payment with taxable and non-taxable parts.")
    print("Expected: 9.75% tax only on taxable items\n")
    
    try:
        # Create regular customer
        customer_id = service.create_customer(
            "Cash Payment Customer",
            "555-9999"
        )
        print(f"Created customer (ID: {customer_id})")
        
        # Mixed line items
        line_items = [
            {'amount': 100.00, 'taxable': 1},  # $100 taxable parts
            {'amount': 50.00, 'taxable': 0},   # $50 non-taxable parts
            {'amount': 75.00, 'taxable': 1},   # $75 labor (taxable)
        ]
        
        subtotal, tax, total = service.calculate_tax(
            customer_id, line_items, payment_method='Cash'
        )
        
        expected_tax = (100.00 + 75.00) * 0.0975  # Only taxable items
        
        print(f"\nTaxable items: $175.00")
        print(f"Non-taxable items: $50.00")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Tax:      ${tax:.2f} (expected: ${expected_tax:.2f})")
        print(f"Total:    ${total:.2f}")
        
        if abs(tax - expected_tax) < 0.01:
            print("\n✓ TEST PASSED: Only taxable items are taxed")
        else:
            print(f"\n✗ TEST FAILED: Expected ${expected_tax:.2f} tax, got ${tax:.2f}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_standard_scenario():
    """Test standard taxable scenario."""
    print("\n--- Standard Purchase Test ---")
    print("This scenario tests a regular customer with standard purchase.")
    print("Expected: 9.75% tax on all taxable items\n")
    
    try:
        # Create regular customer
        customer_id = service.create_customer(
            "Regular Customer",
            "555-1111"
        )
        print(f"Created customer (ID: {customer_id})")
        
        # Line items
        line_items = [
            {'amount': 100.00, 'taxable': 1},  # $100 in parts
            {'amount': 50.00, 'taxable': 1},   # $50 in labor
        ]
        
        subtotal, tax, total = service.calculate_tax(
            customer_id, line_items, payment_method='Credit Card'
        )
        
        expected_tax = 150.00 * 0.0975
        
        print(f"\nTaxable items: $150.00")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Tax:      ${tax:.2f} (expected: ${expected_tax:.2f})")
        print(f"Total:    ${total:.2f}")
        
        if abs(tax - expected_tax) < 0.01:
            print("\n✓ TEST PASSED: Standard 9.75% tax applied")
        else:
            print(f"\n✗ TEST FAILED: Expected ${expected_tax:.2f} tax, got ${tax:.2f}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# MAIN MENU
# ============================================================================

def main_menu():
    """Main menu."""
    while True:
        print_header("Cajun Marine CLI Test Harness")
        print("1. Customer Management")
        print("2. Parts Management")
        print("3. New Engine Inventory")
        print("4. Estimate Management")
        print("5. Ticket Management")
        print("6. Deposit Management")
        print("7. Tax Calculation Testing")
        print("0. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            customer_menu()
        elif choice == '2':
            parts_menu()
        elif choice == '3':
            new_engines_menu()
        elif choice == '4':
            estimates_menu()
        elif choice == '5':
            tickets_menu()
        elif choice == '6':
            deposits_menu()
        elif choice == '7':
            tax_testing_menu()
        elif choice == '0':
            print("\nGoodbye!")
            sys.exit(0)


if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
