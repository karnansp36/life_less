import re
from typing import Optional
from datetime import datetime

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    return True, None

def validate_date(date_string: str, format: str = "%Y-%m-%d") -> bool:
    """Validate date format"""
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False

def sanitize_input(text: str) -> str:
    """Basic input sanitization"""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>{}[\]\\]', '', text)
    # Limit length
    return text[:1000]