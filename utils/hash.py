from passlib.context import CryptContext

# Use pbkdf2_sha256 to avoid bcrypt 72-byte backend limitation issues on this platform
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)