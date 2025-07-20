#backend/schemas.py

from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str

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
    end_time: datetime | None = None # Use '| None' to make it optional
    subclient: str

class BackupJobCreate(BackupJobBase):
    pass

class BackupJob(BackupJobBase):
    id: int
    tenant_id: int

    class Config:
        from_attributes = True # Formerly orm_mode