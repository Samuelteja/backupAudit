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
from pydantic import BaseModel, EmailStr, computed_field, Field
from typing import Any, Dict, List
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

# -- Asset Schemas
class AssetBase(BaseModel):
    asset_name: str
    source_type: str

class AssetCreate(AssetBase):
    pass # For now, creating an asset requires the same info as the base

class Asset(AssetBase):
    id: int
    tenant_id: int
    last_seen: datetime

    class Config:
        from_attributes = True

# --- Asset Schemas for Ingestion ---
class AssetIngest(BaseModel):
    asset_name: str
    source_type: str

class AssetIngestPayload(BaseModel):
    hypervisor_hostname: str
    asset_list: List[AssetIngest]

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

# -- Alert Schemas
class AlertBase(BaseModel):
    live_feed_id: int
    alert_name: str
    severity: str
    event_timestamp: datetime
    details: str | None = None # Allow details to be optional

class AlertCreate(AlertBase):
    pass # The agent sends the base data

class Alert(AlertBase):
    id: int
    tenant_id: int
    is_read: bool

    class Config:
        from_attributes = True

class AlertSummary(BaseModel):
    critical_count_24h: int
    warning_count_24h: int
    new_unread_count: int
    backup_success_rate_24h: float | None = None # Can be None if no jobs ran

class AlertsList(BaseModel):
    unread_alerts: List[Alert]
    read_alerts: List[Alert]

class TopAffectedClient(BaseModel):
    client_name: str
    count: int

class GroupedAlert(BaseModel):
    alert_name: str
    severity: str
    occurrence_count: int
    last_seen: datetime
    top_affected_clients: List[TopAffectedClient]

    class Config:
        from_attributes = True

# --- NEW: AI Schemas ---
class AIFinalAnalysis(BaseModel):
    problem_summary: str
    probable_cause: str
    recommended_action: str

class AITriageResponse(BaseModel):
    is_sufficient: bool
    logs_needed: List[str] = []
    analysis: AIFinalAnalysis | None = None

# --- Agent Task Schemas ---
class TaskResult(BaseModel):
    # This is a placeholder; you can make it more specific if you want
    class Config:
        extra = 'allow'

class AgentTask(BaseModel):
    id: int
    task_type: str
    status: str
    result: Dict[str, Any] | None = None
    parent_task_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AgentTaskUpdatePayload(BaseModel):
    status: str # "complete" or "failed"
    result: Dict[str, Any]