# backend/security.py
"""
This file contains security-related functions, including password hashing and JWT token management.
verify_password(plain, hashed): Checks if a plain password matches a stored hash.
get_password_hash(password): Creates a secure hash from a plain password.
create_access_token(data): Creates a new, expiring JWT for a user session.
"""
import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
# Python library for handling password hashing. It's robust and secure.
from passlib.context import CryptContext

# Here, we create an instance of CryptContext. This is our "hashing configuration".
#
# schemes=["bcrypt"]: We are telling passlib that 'bcrypt' is our default and
#                    preferred hashing algorithm. Bcrypt is a strong, slow, and
#                    industry-standard choice for passwords.
#
# deprecated="auto": This is a powerful feature. If, in the future, we decide
#                    to upgrade to a new hashing algorithm, passlib can automatically
#                    re-hash old passwords when a user logs in, without us having
#                    to write any extra code.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed one.

    Args:
        plain_password: The password provided by the user during login.
        hashed_password: The hash stored in our database.

    Returns:
        True if the passwords match, False otherwise.
    """
    # pwd_context.verify knows how to take the plain password, hash it, and
    # securely compare it to the stored hash.
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password.

    Args:
        password: The plain-text password from the user signup form.

    Returns:
        A securely hashed version of the password, ready to be stored in the DB.
    """
    # pwd_context.hash takes the plain password and returns the bcrypt hash.
    return pwd_context.hash(password)

# Secret key
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def create_access_token(data: dict) -> str:
    """
    Creates a new JWT access token.

    Args:
        data: A dictionary of claims to encode in the token.
              We will use this to store the user's email.

    Returns:
        A signed JWT string.
    """
    # Make a copy of the data to avoid modifying the original dictionary.
    to_encode = data.copy()

    # Calculate the token's expiration time.
    # We use timezone.utc to ensure it's a timezone-aware datetime object.
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add the 'exp' (expiration time) claim to the token data.
    to_encode.update({"exp": expire})
    
    # Use the jose library to encode the token with our data, secret key, and algorithm.
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt