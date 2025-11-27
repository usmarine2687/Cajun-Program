# Cajun Marine Management System

Unified application for managing customers, boats, engines, parts, tickets, estimates, PDFs, and backups.

## Core Files
- `app.py` — Main Tkinter application (navigation, tickets, parts, labor, estimates, backups, PDF export).
- `db/service.py` — Service layer with all CRUD and business logic (tax calculation, totals, deposits).
- `db/db_utils.py` / `init_db.py` — Database initialization and path helpers.
- `schema.sql` — Full database schema (customers, boats, engines, parts, tickets, estimates, mechanics, deposits).
- `pdf_generator.py` — Invoice and estimate PDF generation.
- `backup_utils.py` — Automated and manual backup management.
- `validation.py` — Field validation utilities.

Legacy helper scripts and earlier multi-form GUI modules have been removed to reduce clutter. The single entry point is now `app.py`.

## Setup
```powershell
python init.py   # Ensure schema applied
python app.py    # Launch application
```

## Key Features
- Ticket workflow: parts & labor assignment, automatic tax & totals, deposits, PDFs.
- Inventory: parts with supplier, cost, retail, taxable flag, part numbers; new engines tracking.
- Boat & engine management with extended schema (colors, engine types, outdrive, year).
- Mechanics management (password-protected Settings page).
- Automated backup and restore.

## Next Planned Improvement
Revamp PDF design (see TODO) for branding, clearer totals, inclusion of engine and part number details.

## Notes
- Data stored in `Cajun_Data.db` beside the codebase.
- All SQLite connections use a timeout to mitigate lock errors.
- Louisiana tax rate (9.75%) with exemption rules implemented in service layer.

## Backups
Backups are placed under the `backups/` directory. Use the Backup menu in the GUI to create or restore.

## License
Internal project for Cajun Marine operations.
