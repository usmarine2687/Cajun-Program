CREATE TABLE IF NOT EXISTS Customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    tax_exempt INTEGER DEFAULT 0,
    tax_exempt_certificate TEXT,
    out_of_state INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Boats (
    boat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    make TEXT,
    model TEXT,
    year INTEGER,
    vin TEXT UNIQUE,
    color1 TEXT,
    color2 TEXT,
    color3 TEXT,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

CREATE TABLE IF NOT EXISTS Engines (
    engine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    boat_id INTEGER NOT NULL,
    engine_type TEXT CHECK(engine_type IN ('Inboard', 'Outboard', 'Sterndrive', 'PWC')),
    make TEXT,
    model TEXT,
    hp REAL,
    serial_number TEXT,
    year INTEGER,
    outdrive TEXT,
    FOREIGN KEY (boat_id) REFERENCES Boats(boat_id)
);

CREATE TABLE IF NOT EXISTS NewEngines (
    new_engine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp INTEGER NOT NULL,
    model TEXT NOT NULL,
    serial_number TEXT UNIQUE NOT NULL,
    status TEXT CHECK(status IN ('In Stock', 'Sold', 'Transferred')) DEFAULT 'In Stock',
    customer_id INTEGER,
    boat_id INTEGER,
    date_sold TEXT,
    date_installed TEXT,
    date_transferred TEXT,
    transferred_to TEXT,
    purchase_price REAL,
    sale_price REAL,
    paid_in_full INTEGER DEFAULT 0,
    registered_with_tohatsu INTEGER DEFAULT 0,
    registration_date TEXT,
    notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (boat_id) REFERENCES Boats(boat_id)
);

CREATE TABLE IF NOT EXISTS Mechanics (
    mechanic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    hourly_rate REAL NOT NULL,
    phone TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS Parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_number TEXT,
    name TEXT NOT NULL,
    stock_quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    supplier_name TEXT,
    cost_from_supplier REAL,
    retail_price REAL,
    taxable INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    boat_id INTEGER NOT NULL,
    engine_id INTEGER,
    description TEXT,
    status TEXT CHECK(status IN ('Open', 'Working', 'Awaiting Parts', 'Awaiting Customer', 'Awaiting Payment', 'Awaiting Pickup', 'Closed')) DEFAULT 'Open',
    date_opened DATE DEFAULT CURRENT_DATE,
    date_closed DATE,
    payment_method TEXT,
    subtotal REAL DEFAULT 0,
    tax_amount REAL DEFAULT 0,
    total REAL DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (boat_id) REFERENCES Boats(boat_id),
    FOREIGN KEY (engine_id) REFERENCES Engines(engine_id)
);

CREATE TABLE IF NOT EXISTS TicketAssignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    mechanic_id INTEGER NOT NULL,
    hours_worked REAL DEFAULT 0,
    work_description TEXT,
    labor_rate REAL DEFAULT 0,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id),
    FOREIGN KEY (mechanic_id) REFERENCES Mechanics(mechanic_id)
);

CREATE TABLE IF NOT EXISTS TicketParts (
    ticket_part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity_used INTEGER NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id),
    FOREIGN KEY (part_id) REFERENCES Parts(part_id)
);

CREATE TABLE IF NOT EXISTS Estimates (
    estimate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    boat_id INTEGER,
    engine_id INTEGER,
    date_created TEXT NOT NULL,
    insurance_company TEXT,
    claim_number TEXT,
    notes TEXT,
    subtotal REAL DEFAULT 0,
    tax_amount REAL DEFAULT 0,
    total REAL DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (boat_id) REFERENCES Boats(boat_id),
    FOREIGN KEY (engine_id) REFERENCES Engines(engine_id)
);

CREATE TABLE IF NOT EXISTS EstimateLineItems (
    line_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    item_type TEXT CHECK(item_type IN ('part', 'labor')),
    description TEXT,
    quantity REAL DEFAULT 1,
    unit_price REAL DEFAULT 0,
    line_total REAL DEFAULT 0,
    FOREIGN KEY (estimate_id) REFERENCES Estimates(estimate_id)
);

CREATE TABLE IF NOT EXISTS Deposits (
    deposit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT,
    notes TEXT,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id)
);