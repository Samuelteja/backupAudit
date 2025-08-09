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
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List
import models
import schemas
import security
import json
from services import ai_service, prompt_service

""" User Management Start """

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).options(joinedload(models.User.tenant)).filter(models.User.email == email).first()

def create_user_and_tenant(db: Session, user_data: schemas.UserCreateWithTenant):
    db_tenant = models.Tenant(name=user_data.tenant_name, owner_id=0)
    hashed_password = security.get_password_hash(user_data.password)
    db_user = models.User(
        email=user_data.email, 
        hashed_password=hashed_password,
        role='owner',
        tenant=db_tenant
    )
    db.add(db_user)
    db.commit()
    db_tenant.owner_id = db_user.id
    db.commit()
    
    db.refresh(db_user)
    
    return db_user

def create_tenant_user(db: Session, user_data: schemas.UserInvite, tenant_id: int):
    hashed_password = security.get_password_hash("changeme") 
    db_user = models.User(
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        tenant_id=tenant_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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
    return db.query(models.DataSource).filter(models.DataSource.api_key == api_key).first()

""" User Management End """

""" Job Management Start """
def get_jobs_by_tenant(db: Session, tenant_id: int):
    """Gets all backup jobs for a given tenant."""
    return db.query(models.BackupJob).join(models.DataSource).filter(models.DataSource.tenant_id == tenant_id).all()

def get_job_by_id_for_tenant(db: Session, job_db_id: int, tenant_id: int) -> models.BackupJob | None:
    # This query joins the BackupJob table with the DataSource table.
    # It then filters to find a job that has the correct database ID
    # AND is linked to a data source that belongs to the correct tenant_id.
    return db.query(models.BackupJob).join(models.DataSource).filter(
        models.BackupJob.id == job_db_id,
        models.DataSource.tenant_id == tenant_id
    ).first()

""" Task Management Start """
def create_agent_task(
    db: Session, 
    data_source_id: int, 
    task_type: str, 
    payload: dict, 
    parent_task_id: int | None = None
) -> models.AgentTask:
    new_task = models.AgentTask(
        data_source_id=data_source_id,
        task_type=task_type,
        task_payload=payload,
        status="pending",
        parent_task_id=parent_task_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def get_pending_task_for_agent(db: Session, data_source_id: int) -> models.AgentTask | None:
    """Gets the oldest pending task for a specific agent."""
    return db.query(models.AgentTask).filter(
        models.AgentTask.data_source_id == data_source_id,
        models.AgentTask.status == "pending"
    ).order_by(models.AgentTask.created_at).first()

def get_task_by_id(db: Session, task_id: int, tenant_id: int) -> models.AgentTask | None:
    """Gets a specific task, ensuring it belongs to the correct tenant for security."""
    return db.query(models.AgentTask).join(models.DataSource).filter(
        models.AgentTask.id == task_id,
        models.DataSource.tenant_id == tenant_id
    ).first()

def update_task_status(db: Session, task_id: int, new_status: str, result: dict | None = None) -> models.AgentTask | None:
    """Updates the status, result, and error details of a task."""
    task = db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()
    if task:
        task.status = new_status
        if result is not None:
            if new_status == "failed":
                task.error_details = str(result.get("error", "Unknown agent error"))
            else:
                task.result = result
        
        db.commit()
        db.refresh(task)
    return task

def get_completed_child_task(db: Session, parent_task_id: int) -> models.AgentTask | None:
    """
    Finds a 'complete' child task for a given parent task ID.

    This is used in the multi-stage analysis to find the result of a 
    follow-up task, like fetching specific logs.

    Args:
        db: The SQLAlchemy database session.
        parent_task_id: The ID of the original, parent task.

    Returns:
        The completed child AgentTask object if found, otherwise None.
    """
    return db.query(models.AgentTask).filter(
        models.AgentTask.parent_task_id == parent_task_id,
        models.AgentTask.status == "complete"
    ).first()

# in backend/crud.py

def lock_task_for_triage(db: Session, task: models.AgentTask) -> bool:
    """
    Atomically sets the task status to 'trieaging' to prevent race conditions.
    
    Returns:
        True if the lock was acquired, False if it was already locked.
    """
    # This query finds a task that is 'complete' and ready for triage.
    # with_for_update() locks the row in the database until the transaction is committed.
    locked_task = db.query(models.AgentTask).filter(
        models.AgentTask.id == task.id,
        models.AgentTask.status == 'complete' 
    ).with_for_update().first()

    if locked_task:
        locked_task.status = 'trieaging'
        db.commit()
        return True
    return False

""" Task Management End """   
""" AI Triage Management Start """

def perform_ai_triage(db: Session, task: models.AgentTask) -> schemas.AITriageResponse:
    # ... (code to craft the prompt is exactly the same) ...
    job_details = task.result
    failure_summary = job_details.get("failure_summary", "No summary available.")
    formatted_events = "\n".join([f"- {evt.get('message')}" for evt in job_details.get("events", [])[-10:]])
    
    prompt = prompt_service.get_triage_prompt(failure_summary, formatted_events)
    system_prompt = "You are an expert system that responds only in valid JSON format."

    try:
        # Call the new, smart service function that returns a dictionary
        ai_data = ai_service.get_structured_ai_analysis(prompt, system_prompt=system_prompt)
        print("ai data in ai triage:", ai_data)
        # Validate the dictionary against our Pydantic schema
        triage_result = schemas.AITriageResponse(**ai_data)
        return triage_result
    except Exception as e:
        print(f"ERROR: AI Triage failed: {e}")
        # Default to needing more logs if the AI service fails for any reason
        return schemas.AITriageResponse(
            is_sufficient=False, 
            logs_needed=["JobManager.log", "CVD.log"]
        )

def perform_ai_deep_analysis(db: Session, parent_task: models.AgentTask, child_task: models.AgentTask) -> dict:
    # ... (code to craft the final, deep-dive prompt is the same) ...
    initial_data = parent_task.result
    log_data = child_task.result
    formatted_logs = "\n".join([f"{log_name}:\n{content}" for log_name, content in log_data.items()])
    
    prompt = prompt_service.get_deep_analysis_prompt(initial_data, log_data)
    system_prompt = "You are an expert system that responds only in valid JSON."

    try:
        ai_analysis = ai_service.get_structured_ai_analysis(prompt, system_prompt=system_prompt)
        print("ai deep data in ai triage:", ai_analysis)
        validated_analysis = schemas.AIFinalAnalysis(**ai_analysis)
        return validated_analysis.model_dump()
    except Exception as e:
        print(f"ERROR: AI Deep Analysis failed: {e}")
        return {
            "problem_summary": "AI Analysis Failed",
            "probable_cause": f"The AI service failed to return a valid analysis. Error: {e}",
            "recommended_action": "Please check the Hokage backend logs for more details."
        }

""" AI Triage Management End """    
""" Job Management End """

""" Asset Management Start """

def delete_assets_by_tenant(db: Session, tenant_id: int):
    """
    Deletes all assets associated with a specific tenant.
    This is the "pruning" step of the reconciliation process.
    """
    db.query(models.Asset).filter(models.Asset.tenant_id == tenant_id).delete(synchronize_session=False)

def bulk_create_assets(db: Session, assets: List[schemas.AssetIngest], tenant_id: int):
    """
    Efficiently bulk inserts a list of new assets for a tenant.
    """
    new_assets = [
        models.Asset(
            asset_name=asset.asset_name,
            source_type=asset.source_type,
            tenant_id=tenant_id
        )
        for asset in assets
    ]
    db.bulk_save_objects(new_assets)

def get_unprotected_assets_for_tenant(db: Session, tenant_id: int) -> List[str]:
    """
    The "brains" of the analysis. Finds assets that exist in vCenter
    but not in Commvault for a specific tenant.
    """
    # 1. Get all assets discovered from vCenter for this tenant
    vcenter_assets_query = db.query(models.Asset.asset_name).filter(
        models.Asset.tenant_id == tenant_id,
        models.Asset.source_type == 'vcenter'
    )
    vcenter_assets_set = {name for name, in vcenter_assets_query}

    # 2. Get all assets protected by Commvault for this tenant
    commvault_assets_query = db.query(models.Asset.asset_name).filter(
        models.Asset.tenant_id == tenant_id,
        models.Asset.source_type == 'commvault'
    )
    commvault_assets_set = {name for name, in commvault_assets_query}

    # 3. Calculate the difference, we have to uncomment this line below
    # and comment the one below it to get the unprotected assets.
    # unprotected_assets = vcenter_assets_set - commvault_assets_set
    unprotected_assets = commvault_assets_set - vcenter_assets_set

    return sorted(list(unprotected_assets))

""" Asset Management End """

""" Alert Management Start """

def upsert_alerts(db: Session, alerts: List[schemas.AlertCreate], tenant_id: int) -> int:
    """
    Efficiently inserts new alerts while ignoring duplicates based on live_feed_id.

    Returns:
        The number of newly created alerts.
    """
    # 1. Get all live_feed_ids for this tenant that are already in our database.
    #    Putting them in a set provides a very fast (O(1)) lookup.
    existing_ids_query = db.query(models.Alert.live_feed_id).filter(models.Alert.tenant_id == tenant_id)
    existing_ids = {id_tuple[0] for id_tuple in existing_ids_query}

    # 2. Filter the incoming payload to find only the alerts we haven't seen before.
    alerts_to_create = []
    for alert_data in alerts:
        if alert_data.live_feed_id not in existing_ids:
            # Create a new SQLAlchemy model instance for the new alert
            new_alert = models.Alert(
                live_feed_id=alert_data.live_feed_id,
                alert_name=alert_data.alert_name,
                severity=alert_data.severity,
                event_timestamp=alert_data.event_timestamp,
                details=alert_data.details,
                tenant_id=tenant_id
            )
            alerts_to_create.append(new_alert)

    # 3. If there are any new alerts, bulk insert them for high efficiency.
    if alerts_to_create:
        db.bulk_save_objects(alerts_to_create)
        db.commit()
        return len(alerts_to_create)
    
    return 0 # No new alerts were created

def delete_alerts_by_tenant(db: Session, tenant_id: int):
    """
    Deletes all alerts associated with a specific tenant.
    This is the "pruning" step of the alert reconciliation process.
    """
    db.query(models.Alert).filter(models.Alert.tenant_id == tenant_id).delete(synchronize_session=False)
    # The 'synchronize_session=False' is a performance optimization for bulk deletes.

def bulk_create_alerts(db: Session, alerts: List[schemas.AlertCreate], tenant_id: int):
    """
    Efficiently bulk inserts a list of new alerts for a tenant.
    """
    new_alerts = [
        models.Alert(
            alert_name=alert.alert_name,
            severity=alert.severity,
            event_timestamp=alert.event_timestamp,
            details=alert.details,
            tenant_id=tenant_id
        )
        for alert in alerts
    ]
    # The bulk_save_objects method is highly efficient for inserting many rows.
    db.bulk_save_objects(new_alerts)

def get_alert_summary_for_tenant(db: Session, tenant_id: int) -> dict:
    """
    Calculates high-level KPI statistics for a tenant's alerts and jobs.
    """
    # Define the time window (last 24 hours)
    time_24_hours_ago = datetime.utcnow() - timedelta(hours=24)

    # 1. Count Critical Alerts in the last 24 hours
    critical_count = db.query(models.Alert).filter(
        models.Alert.tenant_id == tenant_id,
        models.Alert.severity == 'Critical',
        models.Alert.event_timestamp >= time_24_hours_ago
    ).count()

    # 2. Count Warning Alerts in the last 24 hours
    warning_count = db.query(models.Alert).filter(
        models.Alert.tenant_id == tenant_id,
        models.Alert.severity == 'Warning',
        models.Alert.event_timestamp >= time_24_hours_ago
    ).count()

    # 3. Count all unread alerts
    new_unread_count = db.query(models.Alert).filter(
        models.Alert.tenant_id == tenant_id,
        models.Alert.is_read == False
    ).count()

    # 4. Calculate Backup Success Rate
    total_jobs = db.query(models.BackupJob).join(models.DataSource).filter(
        models.DataSource.tenant_id == tenant_id,
        models.BackupJob.start_time >= time_24_hours_ago
    ).count()
    print(f"Total jobs in the last 24 hours: {total_jobs}")

    successful_jobs = db.query(models.BackupJob).join(models.DataSource).filter(
        models.DataSource.tenant_id == tenant_id,
        models.BackupJob.status.ilike('%completed%'), # Use ilike for case-insensitivity
        models.BackupJob.start_time >= time_24_hours_ago
    ).count()
    print(f"Successful jobs in the last 24 hours: {successful_jobs}")
    backup_success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else None

    return {
        "critical_count_24h": critical_count,
        "warning_count_24h": warning_count,
        "new_unread_count": new_unread_count,
        "backup_success_rate_24h": backup_success_rate
    }

def mark_alert_as_read(db: Session, alert_id: int, tenant_id: int) -> models.Alert | None:
    """
    Finds an alert by its ID and marks it as read.
    Includes a security check to ensure the alert belongs to the correct tenant.
    """
    # Find the alert, ensuring it belongs to the user's tenant to prevent
    # one user from acknowledging another tenant's alerts.
    alert_to_update = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.tenant_id == tenant_id
    ).first()

    # If an alert is found, update its 'is_read' status
    if alert_to_update:
        alert_to_update.is_read = True
        db.commit()
        db.refresh(alert_to_update)
        return alert_to_update
    
    # Return None if no matching alert was found
    return None


def get_alerts_for_tenant(db: Session, tenant_id: int, alert_name_filter: str | None = None, severity_filter: str | None = None) -> dict:
    """
    Gets all alerts for a tenant, separated into 'read' and 'unread' lists.
    Orders unread alerts by severity and time to prioritize them.
    """
    unread_query = db.query(models.Alert).filter(
        models.Alert.tenant_id == tenant_id,
        models.Alert.is_read == False
    )

    # Get the 100 most recent read alerts for the history view
    read_query = db.query(models.Alert).filter(
        models.Alert.tenant_id == tenant_id,
        models.Alert.is_read == True
    )

    if alert_name_filter:
        unread_query = unread_query.filter(models.Alert.alert_name == alert_name_filter)
        read_query = read_query.filter(models.Alert.alert_name == alert_name_filter)

    if severity_filter:
        unread_query = unread_query.filter(models.Alert.severity == severity_filter)
        read_query = read_query.filter(models.Alert.severity == severity_filter)

    # Execute the final queries with ordering and limits
    unread_alerts = unread_query.order_by(models.Alert.severity, models.Alert.event_timestamp.desc()).all()
    read_alerts = read_query.order_by(models.Alert.event_timestamp.desc()).limit(100).all()

    return {"unread_alerts": unread_alerts, "read_alerts": read_alerts}

def get_grouped_alerts_for_tenant(db: Session, tenant_id: int) -> List[dict]:
    """
    Performs a complex aggregation to group alerts by name and find the
    most frequent problems and the clients they affect most often.
    """
    # This is a complex query, let's build it step-by-step.
    # We want to group by alert name and severity.
    grouped_alerts_query = db.query(
        models.Alert.alert_name,
        models.Alert.severity,
        func.count(models.Alert.id).label("occurrence_count"),
        func.max(models.Alert.event_timestamp).label("last_seen")
    ).filter(
        models.Alert.tenant_id == tenant_id
    ).group_by(
        models.Alert.alert_name,
        models.Alert.severity
    ).order_by(
        desc("occurrence_count")
    ).all()

    # The query above gives us the main stats. Now, for each group,
    # we need a second query to find the top affected clients.
    results = []
    for alert_name, severity, count, last_seen in grouped_alerts_query:
        # For each problem type, find the top 3 noisiest clients.
        # We parse the 'details' string to extract the client name.
        top_clients_query = db.query(
            func.substring(models.Alert.details, 'Client: ([^,;\\n]+)').label("client_name"),
            func.count(models.Alert.id).label("client_count")
        ).filter(
            models.Alert.tenant_id == tenant_id,
            models.Alert.alert_name == alert_name
        ).group_by(
            "client_name"
        ).order_by(
            desc("client_count")
        ).limit(3).all()

        results.append({
            "alert_name": alert_name,
            "severity": severity,
            "occurrence_count": count,
            "last_seen": last_seen,
            "top_affected_clients": [
                {"client_name": name, "count": num} for name, num in top_clients_query if name
            ]
        })
        
    return results

""" Alert Management End """

