"""CLI entry point - delegates to service layer."""
from db import service
from db.init import initialize_database


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry - initializes DB and delegates to service.cli_main."""
    try:
        initialize_database()
    except Exception:
        pass
    service.cli_main(argv)


if __name__ == "__main__":
    main()
