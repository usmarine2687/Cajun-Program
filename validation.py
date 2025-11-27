"""Input validation functions for data integrity."""
import re


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
