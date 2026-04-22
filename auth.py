from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
<<<<<<< HEAD
    return pwd_context.verify(plain_password, hashed_password)
=======
    return pwd_context.verify(plain_password, hashed_password)
>>>>>>> b04b50b8ca3a8d6b8544cae833fe8bb756ca0cc6
