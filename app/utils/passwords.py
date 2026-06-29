import secrets
import string

PASSWORD_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def normalize_password(password: str) -> str:
    return password.strip().upper()


def generate_password(length: int = 8) -> str:
    return "".join(secrets.choice(PASSWORD_CHARS) for _ in range(length))


def is_valid_password(password: str) -> bool:
    normalized = normalize_password(password)
    return (
        len(normalized) == 8
        and any(char in string.ascii_uppercase for char in normalized)
        and any(char.isdigit() for char in normalized)
    )
