# backend/crud.py

# We import Session from SQLAlchemy to use for type hinting. This helps our
# code editor with autocompletion and error checking.
from sqlalchemy.orm import Session

# We import the modules containing our database models, our API schemas,
# and our new security functions.
import models
import schemas
import security

# --- User CRUD Functions ---

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """
    Reads a user from the database based on their email address.

    Args:
        db: The SQLAlchemy database session.
        email: The email address to search for.

    Returns:
        The User model object if found, otherwise None.
    """
    # This is a standard SQLAlchemy query.
    # It queries the User table, filters for a matching email, and returns
    # the first result it finds (or None if no results).
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Creates a new user in the database.

    Args:
        db: The SQLAlchemy database session.
        user: A Pydantic schema object containing the user's email and password.

    Returns:
        The newly created User model object.
    """
    # 1. Take the user's plain-text password and hash it using our security utility.
    hashed_password = security.get_password_hash(user.password)

    # 2. Create an instance of our SQLAlchemy User model.
    #    We pass the email directly, but we use the *hashed* password.
    db_user = models.User(email=user.email, hashed_password=hashed_password)

    # 3. Add the new user object to the database session.
    db.add(db_user)

    # 4. Commit the transaction to permanently save the changes to the database.
    db.commit()

    # 5. Refresh the user object. This updates db_user with any new data that
    #    the database generated, like the auto-incremented 'id' and the default 'created_at'.
    db.refresh(db_user)

    return db_user