# Cajun Marine Management System

Unified application for managing customers, boats, engines, parts, tickets, estimates, PDFs, and backups.

## Core Files
- `app.py` — Main Tkinter application (navigation, tickets, parts, labor, estimates, backups, PDF export).
- `db/service.py` — Central service layer: CRUD, business logic, tax/total calculations, deposits, plus validation, backup utilities, and DB path helpers. Also hosts the CLI entry (`cli_main`).
- `db/init.py` — Unified, idempotent database initializer and lightweight migrations.
- `schema.sql` — Baseline database schema (customers, boats, engines, parts, tickets, estimates, mechanics, deposits).
- `pdf_generator.py` — Invoice and estimate PDF generation.

Legacy helper scripts (old `init.py`, `db/db_utils.py`, `init_db.py`, `backup_utils.py`, `validation.py`) have been consolidated into `db/service.py` and `db/init.py`. The application auto-initializes on startup.

## Setup
```powershell
python app.py    # Launch application (auto-initializes DB and creates a backup)
```

Optional CLI (notes example):
```powershell
python cli.py set-notes 123 "Replaced water pump; customer approved"
python cli.py append-notes 123 "Waiting on pickup"
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
