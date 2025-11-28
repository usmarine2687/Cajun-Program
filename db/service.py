"""
Cajun Marine Service Layer
Centralized business logic and CRUD operations for all entities.
Includes validation, backup utilities, and database helpers.
"""
import sqlite3
import os
import shutil
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
import argparse


# ============================================================================
# DATABASE PATH & UTILITIES
# ============================================================================

def get_db_path():
    """Return the absolute path to the database file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(base_dir), "Cajun_Data.db")

def _format_phone(raw_phone: str) -> str:
    """Format phone as (###)###-#### if it has 10 digits; otherwise return original stripped."""
    if not raw_phone:
        return ''
    digits = ''.join(ch for ch in str(raw_phone) if ch.isdigit())
    if len(digits) == 10:
        return f"({digits[0:3]}){digits[3:6]}-{digits[6:10]}"
    return str(raw_phone).strip()

def ensure_database_exists():
    """Ensure database exists by creating from schema if needed."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_phone(phone):
    """
    Validate phone number format.
    Returns (is_valid, formatted_phone, error_message)
    """
    if not phone or phone.strip() == '':
        return True, '', None  # Empty is OK
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if we have exactly 10 digits
    if len(digits) != 10:
        return False, phone, "Phone number must be 10 digits (e.g., 555-123-4567)"
    
    # Format as (555)123-4567
    formatted = f"({digits[0:3]}){digits[3:6]}-{digits[6:10]}"
    return True, formatted, None


def validate_email(email):
    """
    Validate email format.
    Returns (is_valid, error_message)
    """
    if not email or email.strip() == '':
        return True, None  # Empty is OK
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email.strip()):
        return True, None
    else:
        return False, "Invalid email format (e.g., user@example.com)"


def validate_serial_number(serial):
    """
    Validate serial number (alphanumeric, no special chars except dash/underscore).
    Returns (is_valid, error_message)
    """
    if not serial or serial.strip() == '':
        return False, "Serial number is required"
    
    # Allow alphanumeric, dash, and underscore only
    pattern = r'^[a-zA-Z0-9_-]+$'
    
    if re.match(pattern, serial.strip()):
        return True, None
    else:
        return False, "Serial number can only contain letters, numbers, dashes, and underscores"


def validate_required_field(value, field_name):
    """
    Validate that a required field is not empty.
    Returns (is_valid, error_message)
    """
    if not value or str(value).strip() == '':
        return False, f"{field_name} is required"
    return True, None


def validate_positive_number(value, field_name, allow_zero=False):
    """
    Validate that a number is positive (and optionally allow zero).
    Returns (is_valid, error_message)
    """
    try:
        num = float(value)
        if allow_zero:
            if num < 0:
                return False, f"{field_name} cannot be negative"
        else:
            if num <= 0:
                return False, f"{field_name} must be greater than zero"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def validate_integer(value, field_name, min_value=None, max_value=None):
    """
    Validate that a value is an integer within optional min/max range.
    Returns (is_valid, error_message)
    """
    try:
        num = int(value)
        if min_value is not None and num < min_value:
            return False, f"{field_name} must be at least {min_value}"
        if max_value is not None and num > max_value:
            return False, f"{field_name} must be at most {max_value}"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid integer"


# ============================================================================
# BACKUP UTILITIES
# ============================================================================

def get_backup_dir():
    """Get the backup directory path, create if doesn't exist."""
    backup_dir = Path("c:/Cajun Program/backups")
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def create_backup():
    """
    Create a timestamped backup of the database.
    Returns (success, backup_path, error_message)
    """
    try:
        db_path = get_db_path()
        if not os.path.exists(db_path):
            return False, None, "Database file not found"
        
        backup_dir = get_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"Cajun_Data_backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Clean up old backups (keep last 7 days)
        cleanup_old_backups()
        
        return True, str(backup_path), None
    except Exception as e:
        return False, None, str(e)


def cleanup_old_backups(keep_days=7):
    """Remove backup files older than keep_days."""
    try:
        backup_dir = get_backup_dir()
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        for backup_file in backup_dir.glob("Cajun_Data_backup_*.db"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
    except Exception:
        pass  # Silently fail on cleanup


def list_backups():
    """
    List all available backup files.
    Returns list of tuples: (filename, date_created, size_mb)
    """
    backups = []
    backup_dir = get_backup_dir()
    
    for backup_file in sorted(backup_dir.glob("Cajun_Data_backup_*.db"), reverse=True):
        stat = backup_file.stat()
        date_created = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        size_mb = stat.st_size / (1024 * 1024)
        backups.append((backup_file.name, date_created, size_mb))
    
    return backups


def restore_backup(backup_filename):
    """
    Restore database from a backup file.
    Returns (success, error_message)
    """
    try:
        backup_dir = get_backup_dir()
        backup_path = backup_dir / backup_filename
        
        if not backup_path.exists():
            return False, "Backup file not found"
        
        # Create a backup of the current database before restoring
        db_path = get_db_path()
        if os.path.exists(db_path):
            temp_backup = db_path + ".pre_restore_backup"
            shutil.copy2(db_path, temp_backup)
        
        # Restore the backup
        shutil.copy2(backup_path, db_path)
        
        return True, None
    except Exception as e:
        return False, str(e)


def auto_backup_on_startup():
    """
    Create automatic backup on application startup.
    Returns (success, message)
    """
    success, backup_path, error = create_backup()
    if success:
        return True, f"Auto-backup created: {Path(backup_path).name}"
    else:
        return False, f"Auto-backup failed: {error}"


# ============================================================================
# CONSTANTS
# ============================================================================

TAX_RATE = 0.0975  # 9.75% Tennessee tax rate


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def _get_connection():
    """Get database connection."""
    return sqlite3.connect(get_db_path())


def _dict_factory(cursor, row):
    """Convert row to dictionary."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# ============================================================================
# CUSTOMER OPERATIONS
# ============================================================================

def create_customer(name: str, phone: str = None, email: str = None, 
                   address: str = None, tax_exempt: int = 0,
                   tax_exempt_certificate: str = None, 
                   out_of_state: int = 0) -> int:
    """Create a new customer. Returns customer_id."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Customers (name, phone, email, address, tax_exempt, 
                              tax_exempt_certificate, out_of_state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, email, address, tax_exempt, tax_exempt_certificate, out_of_state))
    conn.commit()
    customer_id = cur.lastrowid
    conn.close()
    return customer_id


def get_customer(customer_id: int) -> Optional[Dict]:
    """Get customer by ID. Returns dict or None."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM Customers WHERE customer_id = ?", (customer_id,))
    result = cur.fetchone()
    conn.close()
    return result


def update_customer(customer_id: int, **fields) -> bool:
    """Update customer fields. Returns success boolean."""
    if not fields:
        return False
    
    allowed_fields = {'name', 'phone', 'email', 'address', 'tax_exempt', 
                     'tax_exempt_certificate', 'out_of_state'}
    updates = {k: v for k, v in fields.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [customer_id]
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE Customers SET {set_clause} WHERE customer_id = ?", values)
    conn.commit()
    success = cur.rowcount > 0
    conn.close()
    return success


def list_customers() -> List[Dict]:
    """List all customers."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM Customers ORDER BY name")
    results = cur.fetchall()
    conn.close()
    return results


# ============================================================================
# PARTS OPERATIONS
# ============================================================================

def create_part(part_number: Optional[str] = None, name: str = "", stock_quantity: int = 0, price: float = 0.0,
               supplier_name: Optional[str] = None, cost_from_supplier: Optional[float] = None,
               retail_price: Optional[float] = None, taxable: int = 1) -> int:
    """Create a new part. Returns part_id."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Parts (part_number, name, stock_quantity, price,
                          supplier_name, cost_from_supplier, retail_price, taxable)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (part_number, name, stock_quantity, price, supplier_name,
          cost_from_supplier, retail_price, taxable))
    conn.commit()
    part_id = cur.lastrowid
    conn.close()
    return part_id


def get_part(part_id: int) -> Optional[Dict]:
    """Get part by ID. Returns dict or None."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM Parts WHERE part_id = ?", (part_id,))
    result = cur.fetchone()
    conn.close()
    return result


def update_part(part_id: int, **fields) -> bool:
    """Update part fields. Returns success boolean."""
    if not fields:
        return False
    
    allowed_fields = {'part_number', 'name', 'stock_quantity', 'price', 'supplier_name', 
                     'cost_from_supplier', 'retail_price', 'taxable'}
    updates = {k: v for k, v in fields.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [part_id]
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE Parts SET {set_clause} WHERE part_id = ?", values)
    conn.commit()
    success = cur.rowcount > 0
    conn.close()
    return success


def list_parts() -> List[Dict]:
    """List all parts."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM Parts ORDER BY name")
    results = cur.fetchall()
    conn.close()
    return results


# ============================================================================
# NEW ENGINE OPERATIONS
# ============================================================================

def create_new_engine(hp: int, model: str, serial_number: str,
                     purchase_price: float = None, notes: str = None) -> int:
    """Create a new engine in inventory. Returns new_engine_id."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO NewEngines (hp, model, serial_number, status, purchase_price, notes)
        VALUES (?, ?, ?, 'In Stock', ?, ?)
    """, (hp, model, serial_number, purchase_price, notes))
    conn.commit()
    engine_id = cur.lastrowid
    conn.close()
    return engine_id


def get_new_engine(new_engine_id: int) -> Optional[Dict]:
    """Get new engine by ID. Returns dict or None."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM NewEngines WHERE new_engine_id = ?", (new_engine_id,))
    result = cur.fetchone()
    conn.close()
    return result


def sell_new_engine(new_engine_id: int, customer_id: int, boat_id: int = None,
                   sale_price: float = None, date_sold: str = None,
                   date_installed: str = None, paid_in_full: int = 0) -> bool:
    """Mark engine as sold to customer. Returns success boolean."""
    if date_sold is None:
        date_sold = datetime.now().strftime('%Y-%m-%d')
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE NewEngines 
        SET status = 'Sold', customer_id = ?, boat_id = ?, sale_price = ?,
            date_sold = ?, date_installed = ?, paid_in_full = ?
        WHERE new_engine_id = ? AND status = 'In Stock'
    """, (customer_id, boat_id, sale_price, date_sold, date_installed, 
          paid_in_full, new_engine_id))
    conn.commit()
    success = cur.rowcount > 0
    conn.close()
    return success


def update_new_engine(new_engine_id: int, **fields) -> bool:
    """Update new engine fields. Returns success boolean."""
    if not fields:
        return False
    
    allowed_fields = {'hp', 'model', 'serial_number', 'status', 'customer_id',
                     'boat_id', 'date_sold', 'date_installed', 'date_transferred',
                     'transferred_to', 'purchase_price', 'sale_price', 'paid_in_full',
                     'registered_with_tohatsu', 'registration_date', 'notes'}
    updates = {k: v for k, v in fields.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [new_engine_id]
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE NewEngines SET {set_clause} WHERE new_engine_id = ?", values)
    conn.commit()
    success = cur.rowcount > 0
    conn.close()
    return success


def list_new_engines(status: str = None) -> List[Dict]:
    """List new engines, optionally filtered by status."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    if status:
        cur.execute("SELECT * FROM NewEngines WHERE status = ? ORDER BY new_engine_id", (status,))
    else:
        cur.execute("SELECT * FROM NewEngines ORDER BY new_engine_id")
    
    results = cur.fetchall()
    conn.close()
    return results


def get_engines_needing_registration() -> List[Dict]:
    """Get engines that need Tohatsu registration (sold, paid, installed >30 days, not registered)."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    cur.execute("""
        SELECT ne.*, c.name as customer_name, c.phone as customer_phone
        FROM NewEngines ne
        LEFT JOIN Customers c ON ne.customer_id = c.customer_id
        WHERE ne.status = 'Sold'
          AND ne.paid_in_full = 1
          AND ne.date_installed IS NOT NULL
          AND ne.date_installed <= ?
          AND ne.registered_with_tohatsu = 0
        ORDER BY ne.date_installed
    """, (thirty_days_ago,))
    
    results = cur.fetchall()
    conn.close()
    return results


# ============================================================================
# TAX CALCULATION
# ============================================================================

def calculate_tax(customer_id: int, line_items: List[Dict], 
                 payment_method: str = None, 
                 new_engine_sale_price: float = 0.0) -> Tuple[float, float, float]:
    """
    Calculate subtotal, tax, and total for a transaction.
    
    Args:
        customer_id: Customer ID
        line_items: List of dicts with keys: 'amount', 'taxable' (0 or 1)
        payment_method: Payment method ('Cash', 'Credit Card', 'Check', etc.)
        new_engine_sale_price: Price of new engine if sold (for out-of-state exemption)
    
    Returns:
        Tuple of (subtotal, tax_amount, total)
    
    Tax Rules:
        1. Tax-exempt customer (has certificate) → 0% tax on everything
        2. Out-of-state customer buying new engine → 0% tax on engine only, 9.75% on other taxable items
        3. Cash payment → Only taxable parts are taxed at 9.75%
        4. Default → 9.75% tax on all taxable items
    """
    customer = get_customer(customer_id)
    if not customer:
        raise ValueError(f"Customer {customer_id} not found")
    
    subtotal = sum(item['amount'] for item in line_items)
    if new_engine_sale_price > 0:
        subtotal += new_engine_sale_price
    
    # Rule 1: Tax-exempt customer
    if customer.get('tax_exempt') == 1 and customer.get('tax_exempt_certificate'):
        return (subtotal, 0.0, subtotal)
    
    # Calculate taxable amount
    taxable_amount = 0.0
    
    # Rule 2: Out-of-state customer with new engine
    if customer.get('out_of_state') == 1 and new_engine_sale_price > 0:
        # New engine is tax-exempt, but other taxable items are taxed
        taxable_amount = sum(item['amount'] for item in line_items if item.get('taxable', 1) == 1)
    else:
        # Include all taxable items (engine + parts/labor)
        if new_engine_sale_price > 0:
            taxable_amount = new_engine_sale_price
        taxable_amount += sum(item['amount'] for item in line_items if item.get('taxable', 1) == 1)
    
    # Rule 3: Cash payment - already handled above (only taxable items included)
    # Rule 4: Default - already handled above (all taxable items included)
    
    tax_amount = round(taxable_amount * TAX_RATE, 2)
    total = round(subtotal + tax_amount, 2)
    
    return (subtotal, tax_amount, total)


# ============================================================================
# ESTIMATE OPERATIONS
# ============================================================================

def create_estimate(customer_id: int, boat_id: int = None, engine_id: int = None,
                   insurance_company: str = None, claim_number: str = None,
                   notes: str = None) -> int:
    """Create a new estimate. Returns estimate_id."""
    date_created = datetime.now().strftime('%Y-%m-%d')
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Estimates (customer_id, boat_id, engine_id, date_created,
                              insurance_company, claim_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, boat_id, engine_id, date_created, insurance_company, 
          claim_number, notes))
    conn.commit()
    estimate_id = cur.lastrowid
    conn.close()
    return estimate_id


def add_estimate_line_item(estimate_id: int, item_type: str, description: str,
                          quantity: float = 1.0, unit_price: float = 0.0) -> int:
    """Add line item to estimate. Returns line_item_id."""
    if item_type not in ('part', 'labor'):
        raise ValueError("item_type must be 'part' or 'labor'")
    
    line_total = round(quantity * unit_price, 2)
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO EstimateLineItems (estimate_id, item_type, description, 
                                       quantity, unit_price, line_total)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (estimate_id, item_type, description, quantity, unit_price, line_total))
    conn.commit()
    line_item_id = cur.lastrowid
    conn.close()
    return line_item_id


def calculate_estimate_totals(estimate_id: int) -> Tuple[float, float, float]:
    """Calculate and update estimate totals. Returns (subtotal, tax, total)."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    # Get estimate
    cur.execute("SELECT * FROM Estimates WHERE estimate_id = ?", (estimate_id,))
    estimate = cur.fetchone()
    if not estimate:
        conn.close()
        raise ValueError(f"Estimate {estimate_id} not found")
    
    # Get line items
    cur.execute("""
        SELECT * FROM EstimateLineItems 
        WHERE estimate_id = ? 
        ORDER BY line_item_id
    """, (estimate_id,))
    line_items = cur.fetchall()
    
    # Build line items for tax calculation
    tax_line_items = [{'amount': item['line_total'], 'taxable': 1} for item in line_items]
    
    # Calculate tax
    subtotal, tax_amount, total = calculate_tax(
        estimate['customer_id'], 
        tax_line_items,
        payment_method=None,
        new_engine_sale_price=0.0
    )
    
    # Update estimate
    cur.execute("""
        UPDATE Estimates 
        SET subtotal = ?, tax_amount = ?, total = ?
        WHERE estimate_id = ?
    """, (subtotal, tax_amount, total, estimate_id))
    
    conn.commit()
    conn.close()
    
    return (subtotal, tax_amount, total)


def get_estimate_details(estimate_id: int) -> Optional[Dict]:
    """Get estimate with all line items."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    # Get estimate
    cur.execute("""
        SELECT e.*, c.name as customer_name, c.phone as customer_phone,
               b.make as boat_make, b.model as boat_model
        FROM Estimates e
        LEFT JOIN Customers c ON e.customer_id = c.customer_id
        LEFT JOIN Boats b ON e.boat_id = b.boat_id
        WHERE e.estimate_id = ?
    """, (estimate_id,))
    estimate = cur.fetchone()
    
    if not estimate:
        conn.close()
        return None
    
    # Get line items
    cur.execute("""
        SELECT * FROM EstimateLineItems 
        WHERE estimate_id = ? 
        ORDER BY line_item_id
    """, (estimate_id,))
    estimate['line_items'] = cur.fetchall()
    
    conn.close()
    return estimate


def list_estimates() -> List[Dict]:
    """List all estimates."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("""
        SELECT e.*, c.name as customer_name
        FROM Estimates e
        LEFT JOIN Customers c ON e.customer_id = c.customer_id
        ORDER BY e.date_created DESC
    """)
    results = cur.fetchall()
    conn.close()
    return results


# ============================================================================
# TICKET OPERATIONS
# ============================================================================

def create_ticket(customer_id: int, boat_id: int, engine_id: int = None,
                 description: str = None) -> int:
    """Create a new ticket. Returns ticket_id."""
    date_opened = datetime.now().strftime('%Y-%m-%d')
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Tickets (customer_id, boat_id, engine_id, description, customer_notes,
                           date_opened, status)
        VALUES (?, ?, ?, ?, NULL, ?, 'Open')
    """, (customer_id, boat_id, engine_id, description, date_opened))
    conn.commit()
    ticket_id = cur.lastrowid
    conn.close()
    return ticket_id


def update_ticket_status(ticket_id: int, new_status: str) -> bool:
    """Update ticket status. Returns success boolean."""
    valid_statuses = ['Open', 'Working', 'Awaiting Parts', 'Awaiting Customer', 
                     'Awaiting Payment', 'Awaiting Pickup', 'Closed']
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
    
    conn = _get_connection()
    cur = conn.cursor()
    
    # If closing ticket, set date_closed
    if new_status == 'Closed':
        date_closed = datetime.now().strftime('%Y-%m-%d')
        cur.execute("""
            UPDATE Tickets 
            SET status = ?, date_closed = ?
            WHERE ticket_id = ?
        """, (new_status, date_closed, ticket_id))
    else:
        cur.execute("""
            UPDATE Tickets 
            SET status = ?
            WHERE ticket_id = ?
        """, (new_status, ticket_id))
    
    conn.commit()
    success = cur.rowcount > 0
    conn.close()
    return success


def add_ticket_part(ticket_id: int, part_id: int, quantity: int, price_override: float = None) -> int:
    """Add part to ticket with optional price override. Returns ticket_part_id."""
    conn = _get_connection()
    cur = conn.cursor()
    
    if price_override is not None:
        # Use override price
        cur.execute("""
            INSERT INTO TicketParts (ticket_id, part_id, quantity_used, price)
            VALUES (?, ?, ?, ?)
        """, (ticket_id, part_id, quantity, price_override))
    else:
        # Use default part price
        cur.execute("""
            INSERT INTO TicketParts (ticket_id, part_id, quantity_used)
            VALUES (?, ?, ?)
        """, (ticket_id, part_id, quantity))
    
    conn.commit()
    ticket_part_id = cur.lastrowid
    conn.close()
    return ticket_part_id


def add_ticket_labor(ticket_id: int, mechanic_id: int, hours: float,
                    work_description: str = None, labor_rate: float = None) -> int:
    """Add labor to ticket. Returns assignment_id."""
    conn = _get_connection()
    cur = conn.cursor()
    
    # If no labor rate provided, determine customer rate based on engine class and LaborRates table
    if labor_rate is None:
        # Determine engine class for this ticket
        cur.execute("SELECT engine_id FROM Tickets WHERE ticket_id = ?", (ticket_id,))
        tr = cur.fetchone()
        engine_class = None
        if tr and tr[0]:
            cur.execute("SELECT engine_type FROM Engines WHERE engine_id = ?", (tr[0],))
            er = cur.fetchone()
            eng_type = (er[0].strip().lower() if er and er[0] else '').lower()
            # Normalize common labels
            if 'outboard' in eng_type:
                engine_class = 'outboard'
            elif 'inboard' in eng_type:
                engine_class = 'inboard'
            elif 'stern' in eng_type or 'sterndrive' in eng_type:
                engine_class = 'sterndrive'
            elif 'pwc' in eng_type or 'jetski' in eng_type:
                engine_class = 'pwc'
        # Fetch current labor rates (create defaults if missing)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS LaborRates (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                outboard REAL NOT NULL,
                inboard REAL NOT NULL,
                sterndrive REAL NOT NULL,
                pwc REAL NOT NULL
            )
        """)
        conn.commit()
        cur.execute("SELECT outboard, inboard, sterndrive, pwc FROM LaborRates WHERE id = 1")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO LaborRates (id, outboard, inboard, sterndrive, pwc) VALUES (1, 100.0, 120.0, 120.0, 120.0)")
            conn.commit()
            row = (100.0, 120.0, 120.0, 120.0)
        rates = {
            'outboard': float(row[0]),
            'inboard': float(row[1]),
            'sterndrive': float(row[2]),
            'pwc': float(row[3])
        }
        if engine_class and engine_class in rates:
            labor_rate = rates[engine_class]
        else:
            # Fallback: use mechanic's own hourly rate if available; else default outboard rate
            cur.execute("SELECT hourly_rate FROM Mechanics WHERE mechanic_id = ?", (mechanic_id,))
            mr = cur.fetchone()
            labor_rate = float(mr[0]) if mr and mr[0] is not None else rates['outboard']
    
    cur.execute("""
        INSERT INTO TicketAssignments (ticket_id, mechanic_id, hours_worked, 
                                       work_description, labor_rate)
        VALUES (?, ?, ?, ?, ?)
    """, (ticket_id, mechanic_id, hours, work_description, labor_rate))
    conn.commit()
    assignment_id = cur.lastrowid
    conn.close()
    return assignment_id


def calculate_ticket_totals(ticket_id: int, payment_method: str = None,
                           new_engine_id: int = None) -> Tuple[float, float, float]:
    """Calculate and update ticket totals. Returns (subtotal, tax, total)."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    # Get ticket
    cur.execute("SELECT * FROM Tickets WHERE ticket_id = ?", (ticket_id,))
    ticket = cur.fetchone()
    if not ticket:
        conn.close()
        raise ValueError(f"Ticket {ticket_id} not found")
    
    # Get parts
    cur.execute("""
        SELECT tp.quantity_used, p.price, p.taxable
        FROM TicketParts tp
        JOIN Parts p ON tp.part_id = p.part_id
        WHERE tp.ticket_id = ?
    """, (ticket_id,))
    parts = cur.fetchall()
    
    # Get labor
    cur.execute("""
        SELECT hours_worked, labor_rate
        FROM TicketAssignments
        WHERE ticket_id = ?
    """, (ticket_id,))
    labor = cur.fetchall()
    
    # Build line items
    line_items = []
    
    # Add parts
    for part in parts:
        line_items.append({
            'amount': part['quantity_used'] * part['price'],
            'taxable': part['taxable']
        })
    
    # Add labor (always taxable)
    for l in labor:
        line_items.append({
            'amount': l['hours_worked'] * l['labor_rate'],
            'taxable': 1
        })
    
    # Check for new engine sale
    new_engine_sale_price = 0.0
    if new_engine_id:
        cur.execute("SELECT sale_price FROM NewEngines WHERE new_engine_id = ?", (new_engine_id,))
        result = cur.fetchone()
        if result and result['sale_price']:
            new_engine_sale_price = result['sale_price']
    
    # Calculate tax
    subtotal, tax_amount, total = calculate_tax(
        ticket['customer_id'],
        line_items,
        payment_method=payment_method,
        new_engine_sale_price=new_engine_sale_price
    )
    
    # Update ticket
    cur.execute("""
        UPDATE Tickets 
        SET subtotal = ?, tax_amount = ?, total = ?, payment_method = ?
        WHERE ticket_id = ?
    """, (subtotal, tax_amount, total, payment_method, ticket_id))
    
    conn.commit()
    conn.close()
    
    return (subtotal, tax_amount, total)


def get_ticket_details(ticket_id: int) -> Optional[Dict]:
    """Get ticket with all details (parts, labor, customer, boat, engine)."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    # Get ticket
    cur.execute("""
        SELECT t.*, c.name as customer_name, c.phone as customer_phone,
               b.make as boat_make, b.model as boat_model
        FROM Tickets t
        LEFT JOIN Customers c ON t.customer_id = c.customer_id
        LEFT JOIN Boats b ON t.boat_id = b.boat_id
        WHERE t.ticket_id = ?
    """, (ticket_id,))
    ticket = cur.fetchone()
    
    if not ticket:
        conn.close()
        return None
    
    # Get parts and enrich with computed fields expected by PDF generator
    cur.execute("""
        SELECT tp.ticket_part_id, tp.part_id, tp.quantity_used,
               p.part_number, p.name as part_name, p.price, p.taxable
        FROM TicketParts tp
        JOIN Parts p ON tp.part_id = p.part_id
        WHERE tp.ticket_id = ?
    """, (ticket_id,))
    raw_parts = cur.fetchall()
    parts_enriched = []
    for rp in raw_parts:
        line_total = (rp['quantity_used'] * rp['price']) if rp.get('quantity_used') and rp.get('price') is not None else 0.0
        parts_enriched.append({
            'ticket_part_id': rp['ticket_part_id'],
            'part_id': rp['part_id'],
            'part_name': rp['part_name'],
            'part_number': rp.get('part_number'),
            'price': rp['price'],
            'quantity_used': rp['quantity_used'],
            'quantity': rp['quantity_used'],  # alias for PDF code
            'line_total': line_total,
            'taxable': rp.get('taxable', 1)
        })
    ticket['parts'] = parts_enriched
    
    # Get labor and enrich
    cur.execute("""
        SELECT ta.assignment_id, ta.mechanic_id, ta.hours_worked, ta.work_description, ta.labor_rate,
               m.name as mechanic_name
        FROM TicketAssignments ta
        JOIN Mechanics m ON ta.mechanic_id = m.mechanic_id
        WHERE ta.ticket_id = ?
    """, (ticket_id,))
    raw_labor = cur.fetchall()
    labor_enriched = []
    for rl in raw_labor:
        labor_total = (rl['hours_worked'] * rl['labor_rate']) if rl.get('hours_worked') and rl.get('labor_rate') is not None else 0.0
        labor_enriched.append({
            'assignment_id': rl['assignment_id'],
            'mechanic_id': rl['mechanic_id'],
            'mechanic_name': rl['mechanic_name'],
            'work_description': rl.get('work_description', ''),
            'hours_worked': rl['hours_worked'],
            'labor_rate': rl['labor_rate'],
            'labor_total': labor_total
        })
    ticket['labor'] = labor_enriched
    
    conn.close()
    return ticket

def _ensure_ticket_notes_column():
    """Ensure the Tickets table has customer_notes column."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(Tickets)')
    cols = [row[1] for row in cur.fetchall()]
    if 'customer_notes' not in cols:
        cur.execute('ALTER TABLE Tickets ADD COLUMN customer_notes TEXT')
        conn.commit()
    conn.close()

def set_ticket_notes(ticket_id: int, notes: str) -> None:
    """Set or update the Notes (Tickets.description) for a ticket."""
    _ensure_ticket_notes_column()
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Tickets SET customer_notes = ? WHERE ticket_id = ?", (notes, ticket_id))
    conn.commit()
    conn.close()


def list_tickets(status: Optional[str] = None) -> List[Dict]:
    """List tickets, optionally filtered by status."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    if status:
        cur.execute("""
            SELECT t.*, c.name as customer_name, b.make as boat_make, b.model as boat_model
            FROM Tickets t
            LEFT JOIN Customers c ON t.customer_id = c.customer_id
            LEFT JOIN Boats b ON t.boat_id = b.boat_id
            WHERE t.status = ?
            ORDER BY t.date_opened DESC
        """, (status,))
    else:
        cur.execute("""
            SELECT t.*, c.name as customer_name, b.make as boat_make, b.model as boat_model
            FROM Tickets t
            LEFT JOIN Customers c ON t.customer_id = c.customer_id
            LEFT JOIN Boats b ON t.boat_id = b.boat_id
            ORDER BY t.date_opened DESC
        """)
    
    results = cur.fetchall()
    conn.close()
    return results


# ============================================================================
# DEPOSIT OPERATIONS
# ============================================================================

def add_deposit(ticket_id: int, amount: float, payment_method: Optional[str] = None,
               notes: Optional[str] = None) -> int:
    """Add deposit/payment to ticket. Returns deposit_id."""
    payment_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Deposits (ticket_id, payment_date, amount, payment_method, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (ticket_id, payment_date, amount, payment_method, notes))
    conn.commit()
    last_id = cur.lastrowid if cur.lastrowid is not None else 0
    deposit_id = int(last_id)
    conn.close()
    return deposit_id


def get_ticket_deposits(ticket_id: int) -> List[Dict]:
    """Get all deposits for a ticket."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM Deposits 
        WHERE ticket_id = ? 
        ORDER BY payment_date
    """, (ticket_id,))
    results = cur.fetchall()
    conn.close()
    return results


def calculate_balance_due(ticket_id: int) -> float:
    """Calculate balance due (ticket total - sum of deposits)."""
    conn = _get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    
    # Get ticket total
    cur.execute("SELECT total FROM Tickets WHERE ticket_id = ?", (ticket_id,))
    result = cur.fetchone()
    if not result:
        conn.close()
        return 0.0
    
    ticket_total = result['total'] or 0.0
    
    # Get sum of deposits
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_paid
        FROM Deposits 
        WHERE ticket_id = ?
    """, (ticket_id,))
    result = cur.fetchone()
    total_paid = result['total_paid'] or 0.0
    
    conn.close()
    
    balance_due = round(ticket_total - total_paid, 2)
    return balance_due


# ============================================================================
# CLI ENTRY (optional consolidation)
# ============================================================================

def _cmd_set_notes(args: argparse.Namespace) -> None:
    set_ticket_notes(args.ticket_id, args.notes)
    details = get_ticket_details(args.ticket_id)
    print("Notes updated:")
    print((details.get('customer_notes') if details else '') or '')


def _cmd_append_notes(args: argparse.Namespace) -> None:
    details = get_ticket_details(args.ticket_id)
    existing = (details.get('customer_notes') if details else '') or ''
    combined = (existing + ('\n' if existing else '') + args.notes).strip()
    set_ticket_notes(args.ticket_id, combined)
    print("Notes appended:")
    print(combined)


def cli_main(argv: list[str] | None = None) -> None:
    """Command-line entry that lives within the service layer."""
    parser = argparse.ArgumentParser(description="Cajun Program CLI")
    sub = parser.add_subparsers(dest='command', required=True)

    setp = sub.add_parser('set-notes', help='Set customer notes for a ticket')
    setp.add_argument('ticket_id', type=int)
    setp.add_argument('notes', type=str)
    setp.set_defaults(func=_cmd_set_notes)

    appp = sub.add_parser('append-notes', help='Append to customer notes for a ticket')
    appp.add_argument('ticket_id', type=int)
    appp.add_argument('notes', type=str)
    appp.set_defaults(func=_cmd_append_notes)

    args = parser.parse_args(argv)
    args.func(args)
