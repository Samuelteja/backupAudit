#backend/schemas.py
"""
This file defines the Pydantic schemas for data validation and serialization.
It includes schemas for:

Tenant Schemas:
    Tenant: Defines the standard shape for tenant data in API responses.
User Schemas:
    UserCreateWithTenant: The input schema for the main sign-up form (tenant_name, email, password).
    UserInvite: The input schema for inviting a new user (email, role).
    User: The output schema for all user-related responses, safely excluding the password.
Token Schemas:
    Token: The output schema for the login endpoint (access_token, token_type).
    TokenData: An internal schema to validate the contents of a JWT.
BackupJob Schemas:
    BackupJobCreate: The input schema for the agent ingestion endpoint.
    BackupJob: The output schema for returning job data to the frontend.
"""
from pydantic import BaseModel, EmailStr, computed_field
from typing import List
from datetime import datetime

class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: int
    name: str
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserCreateWithTenant(UserCreate):
    email: EmailStr
    password: str
    tenant_name: str

class UserInvite(UserBase):
    role: str

class User(UserBase):
    id: int
    role: str
    tenant: Tenant

    class Config:
        from_attributes  = True

# -- Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None # '| None' means the field is optional

class BackupJobBase(BaseModel):
    job_id: int
    status: str
    start_time: datetime
    end_time: datetime | None = None
    subclient: str

class BackupJobCreate(BackupJobBase):
    pass

class BackupJob(BackupJobBase):
    id: int

    class Config:
        from_attributes = True

