# backend/models.py
"""
This file defines the SQLAlchemy ORM models for the application.
User class: Defines the users table with columns: id, email, hashed_password, created_at, role, tenant_id.
Tenant class: Defines the tenants table with columns: id, name, owner_id, created_at.
DataSource class: Defines the data_sources table with columns: id, name, hostname, source_type, tenant_id, api_key.
BackupJob class: Defines the backup_jobs table with columns: id, job_id, data_source_id, status, start_time, end_time, subclient.
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from typing import List

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    role = Column(String, nullable=False, server_default="viewer")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant")

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    assets = relationship("Asset", back_populates="tenant")

class DataSource(Base):
    """
    Represents a single source of backup data, e.g., a specific CommServe or Veeam server.
    """
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g., "Production CommServe"
    hostname = Column(String, nullable=False) # e.g., "falconcs.idcprodcet.loc"
    source_type = Column(String, nullable=False) # e.g., "Commvault", "Veeam"
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)

class BackupJob(Base):
    __tablename__ = "backup_jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    status = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True) 
    subclient = Column(String)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    asset_name = Column(String, index=True, nullable=False)
    # Where did this asset info come from? e.g., "vcenter", "commvault"
    source_type = Column(String, index=True, nullable=False) 
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="assets")
