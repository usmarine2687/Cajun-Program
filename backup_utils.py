"""Database backup and restore utilities."""
import os
import shutil
from datetime import datetime
from pathlib import Path
from db.db_utils import get_db_path


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
