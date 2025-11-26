# Cajun Program — Customer GUI

This workspace provides a small Tkinter GUI to create and manage Customers, Boats and Engines in an SQLite database.

Files of interest:

- `init.py` — Initializes the SQLite database using `schema.sql` (creates `Cajun_Data.db`).
- `schema.sql` — DB schema including `Customers` table and related tables.
- `Shop.py` — GUI application. Open this to create and manage Customers, Boats and Engines.
- `verify_db_insert.py` — CLI script that inserts a test customer and prints the inserted row (non-GUI verification).
- `verify_boat_insert.py` — CLI script that inserts a test boat attached to the first available customer and prints the inserted row.
- `verify_engine_insert.py` — CLI script that inserts a test engine attached to the first available boat and prints the inserted row.
 - `verify_ticket_insert.py` — CLI script that inserts a test ticket attached to the first available customer and boat, and prints the inserted row.

Note: Engines now store these fields: `type`, `make`, `model`, `hp`, `serial_number`.

Auto-refresh — creating/updating/deleting customers or boats in one tab automatically refreshes related controls in other tabs (Boats, Engines and Tickets selectors/lists).

How to use
----------

1. Initialize the database (if you haven't already):

   ```powershell
   python init.py
   ```

2. Run the GUI form to create new customers:

   ```powershell
   python Shop.py
   ```

3. For a quick CLI test insertion (non-GUI), run:

   ```powershell
   python verify_db_insert.py
   ```

4. To test boat insertion from CLI (ensure you have at least one customer):

   ```powershell
   python verify_boat_insert.py
   ```

5. To test engine insertion from CLI (ensure you have at least one boat):

   ```powershell
   python verify_engine_insert.py
   ```

   6. To test ticket insertion from CLI (ensure you have at least one customer and one boat):

      ```powershell
      python verify_ticket_insert.py
      ```

Migration note
--------------

If you have an older `Cajun_Data.db` created before the Engine schema was expanded, the GUI will attempt to add missing engine columns at startup using `ALTER TABLE ADD COLUMN`. This is a best-effort migration helper — back up your DB first if you need to preserve data.

6. Customers list view (GUI)

   - Open `Shop.py` and switch to the "Customers" tab.
   - The top of the tab shows a table of existing customers.
   - Select a customer to populate the form below for editing.
   - Use Update to save changes or Delete to remove a selected customer (note: deleting customers may fail if dependent boats/engines exist).
   - Use Refresh (on Boats/Engines tabs) if you made changes elsewhere.
   ```
   ```

Notes
-----

- The GUI stores data into `Cajun_Data.db` next to the code.
- Basic validation is performed on fields (e.g. `Name` required; numeric checks for Year and HP).
