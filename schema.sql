CREATE TABLE IF NOT EXISTS Customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT
);

CREATE TABLE IF NOT EXISTS Boats (
    boat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    make TEXT,
    model TEXT,
    year INTEGER,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

CREATE TABLE IF NOT EXISTS Engines (
    engine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    boat_id INTEGER NOT NULL,
    type TEXT,
    make TEXT,
    model TEXT,
    hp INTEGER,
    serial_number TEXT,
    FOREIGN KEY (boat_id) REFERENCES Boats(boat_id)
);

CREATE TABLE IF NOT EXISTS Mechanics (
    mechanic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    hourly_rate REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Parts (
    part_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    stock_quantity INTEGER NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    boat_id INTEGER NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('Open','Closed','In Progress')) DEFAULT 'Open',
    date_opened DATE DEFAULT CURRENT_DATE,
    date_closed DATE,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (boat_id) REFERENCES Boats(boat_id)
);

CREATE TABLE IF NOT EXISTS TicketAssignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    mechanic_id INTEGER NOT NULL,
    hours_worked REAL,
    work_description TEXT,
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

CREATE TABLE IF NOT EXISTS Payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    tax REAL NOT NULL,
    date_paid DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id)
);