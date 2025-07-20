import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, server_default="viewer")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BackupJob(Base):
    __tablename__ = "backup_jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    status = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True) 
    subclient = Column(String)