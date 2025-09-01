from passlib.context import CryptContext

# Centralized password hashing context per Passlib docs
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a plaintext password.

    Args:
        password: plaintext password
    Returns:
        Password hash string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Args:
        plain_password: plaintext password input
        hashed_password: stored password hash
    Returns:
        True if match, else False
    """
    return pwd_context.verify(plain_password, hashed_password)
