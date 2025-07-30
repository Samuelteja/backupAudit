# backend/crud.py
"""
This file contains the CRUD operations for the application. 
. get_user_by_email(email): Finds a single user by their email address.
. create_user_and_tenant(user_data): Creates both a new user (with 'owner' role) and a new tenant during the initial sign-up.
. create_tenant_user(user_data, tenant_id): Creates a new user (with 'viewer' or 'admin' role) within an existing tenant.
. get_users_by_tenant(tenant_id): Retrieves a list of all users belonging to a specific tenant.
. get_data_source_by_api_key(api_key): Finds a data source by its unique key to authenticate an agent.
"""

from sqlalchemy.orm import Session, joinedload
import models
import schemas
import security

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).options(joinedload(models.User.tenant)).filter(models.User.email == email).first()

def create_user_and_tenant(db: Session, user_data: schemas.UserCreateWithTenant):
    # This is an atomic transaction. If any step fails, the whole thing is rolled back.
    
    # 1. Create the user object (without tenant_id yet) and set their role as 'owner'
    db_tenant = models.Tenant(name=user_data.tenant_name, owner_id=0)
    hashed_password = security.get_password_hash(user_data.password)
    db_user = models.User(
        email=user_data.email, 
        hashed_password=hashed_password,
        role='owner',  # The first user is always the owner
        tenant=db_tenant
    )
    db.add(db_user)
    db.commit()
    db_tenant.owner_id = db_user.id
    db.commit()
    
    db.refresh(db_user)
    
    return db_user

# NEW: Function for an admin to invite a new user
def create_tenant_user(db: Session, user_data: schemas.UserInvite, tenant_id: int):
    # For invited users, we can set a default password or implement a password reset flow later.
    # For now, we'll use a simple, non-secure default.
    hashed_password = security.get_password_hash("changeme") 
    db_user = models.User(
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        tenant_id=tenant_id # Assign to the admin's tenant
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# NEW: Function to get all users for a specific tenant
def get_users_by_tenant(db: Session, tenant_id: int):
    return db.query(models.User).filter(models.User.tenant_id == tenant_id).all()

def get_data_source_by_api_key(db: Session, api_key: str) -> models.DataSource | None:
    """
    Reads a data source from the database based on its unique API key.

    Args:
        db: The SQLAlchemy database session.
        api_key: The API key to search for.

    Returns:
        The DataSource model object if found, otherwise None.
    """
    # This is a standard SQLAlchemy query:
    # 1. Query the DataSource table.
    # 2. Filter for a row where the 'api_key' column matches the provided key.
    # 3. Return the first result found (or None).
    return db.query(models.DataSource).filter(models.DataSource.api_key == api_key).first()

def get_jobs_by_tenant(db: Session, tenant_id: int):
    """Gets all backup jobs for a given tenant."""
    # This is an advanced query that joins across three tables:
    # BackupJob -> DataSource -> Tenant
    return db.query(models.BackupJob).join(models.DataSource).filter(models.DataSource.tenant_id == tenant_id).all()