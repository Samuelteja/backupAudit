# backend/main.py
"""
    This is a FastAPI application for managing users and tenants.
    Summary of Endpoints Created
    Endpoint	Method	Purpose	Authentication
    /api/v1/users/	POST	Sign Up: Creates a new Tenant and a new User with the 'owner' role.	Public
    /api/v1/token	POST	Login: Authenticates a user and provides a JWT.	Public
    /api/v1/users/me	GET	Get My Profile: Returns the details of the currently logged-in user.	JWT Required
    /api/v1/tenant/users	GET	List Team Members: Returns all users belonging to your tenant.	JWT Required
    /api/v1/tenant/users	POST	Invite User: Creates a new user within your tenant.	JWT Required (Admin/Owner only)
    /api/v1/injest/jobs	POST	Data Ingestion: Receives job data from the Naruto agent.	Agent API Key Required

    Dependencies:
        get_db(): Provides a database session to an endpoint.
        get_current_user(token): A security dependency that validates a JWT and returns the corresponding user.
    Public Endpoints:
        POST /api/v1/users/: Sign Up for a new user and tenant.
        POST /api/v1/token: Login for an existing user.
    Protected User Endpoints (JWT Required):
        GET /api/v1/users/me: Get the profile of the currently logged-in user.
        GET /api/v1/tenant/users: List all users in your tenant.
        POST /api/v1/tenant/users: Invite a new user to your tenant (requires admin/owner role).
    Protected Agent Endpoint (API Key Required):
        POST /api/v1/injest/jobs: Allows the Naruto agent to submit backup job data.
    Utility Endpoints:
        GET / and GET /api/v1/health: Simple welcome/health check endpoints.
        GET /api/v1/test_db: An endpoint to verify the database connection.
"""
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, Header
import os
import time
import asyncio
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from jose import JWTError, jwt
from typing import List
from services import ai_service

import database, models, schemas, crud, security

# Basic Setup Details
agent_task_channels = {}
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allow the origins listed above
    allow_credentials=True, # Allow cookies to be included in requests (important for auth later)
    allow_methods=["*"],    # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Allow all headers
)

# DB Session Dependency Start

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/test_db")
def test_database_connection(db: Session = Depends(get_db)):
    """
    An endpoint to verify that a connection to the database can be established
    and a simple query can be performed.
    """
    try:
        # Perform a simple query to get the count of users.
        user_count = db.query(models.User).count()
        return {
            "status": "ok",
            "message": f"Successfully connected to DB. Found {user_count} users."
        }
    except Exception as e:
        # If any database error occurs, return an error message.
        return {
            "status": "error",
            "message": f"Failed to connect to DB: {e}"
        }

# DB Session Dependency End

# Basic API Endpoints Start
@app.get("/")
def read_root():
    return {"message": "Welcome to the Assurance Platform API!"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

# Basic API Endpoints End

# User APIs Start
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=token_data.email)

    if user is None:
        raise credentials_exception
    return user

@app.post("/api/v1/users/", response_model=schemas.User)
def signup_new_user_and_tenant(user: schemas.UserCreateWithTenant, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_user_and_tenant(db=db, user_data=user)

@app.post("/api/v1/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Logs a user in by verifying their password and returning a JWT token.
    FastAPI's OAuth2PasswordRequestForm requires the client to send data with
    a 'username' field and a 'password' field. We will treat 'username' as the email.
    """
    # Step 1: Authenticate the user. We find the user by their email (form_data.username).
    user = crud.get_user_by_email(db, email=form_data.username)

    # Step 2: If the user doesn't exist OR the password is incorrect, raise a 401 Unauthorized error.
    # This is a critical security step. We give a generic error to prevent attackers
    # from figuring out which emails are registered.
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, # 401 Unauthorized
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for token-based auth
        )

    # Step 3: If authentication is successful, create an access token.
    # The 'sub' (subject) claim is a standard JWT claim to identify the user.
    access_token = security.create_access_token(data={"sub": user.email})

    # Step 4: Return the token in the response.
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """
    An endpoint that is protected by authentication.
    It uses the get_current_user dependency. FastAPI will run that dependency first.
    If the dependency succeeds, it will inject the returned user object into this
    function as the 'current_user' parameter.
    If the dependency fails, this function's code will never even be run.
    """
    # The logic is incredibly simple: just return the user object that the
    # dependency has already validated and provided to us.
    return current_user

# NEW: Endpoint for an owner/admin to invite a new user to their tenant
@app.post("/api/v1/tenant/users", response_model=schemas.User, status_code=201)
def invite_new_user(user_invite: schemas.UserInvite, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Role-Based Access Control (RBAC) Check
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to invite users")
    
    # Check if user already exists
    db_user = crud.get_user_by_email(db, email=user_invite.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    return crud.create_tenant_user(db=db, user_data=user_invite, tenant_id=current_user.tenant_id)

# User APIs End

# Backup Job APIs Start

@app.post("/api/v1/injest/jobs")
def injest_backup_jobs(
    # FastAPI will automatically parse the incoming JSON request body
    # into a list of objects that match our BackupJobCreate schema.
    # If the data doesn't match, it will fail with a 422 error.
    jobs: list[schemas.BackupJobCreate],

    # This tells FastAPI to look for a custom HTTP header named 'x-agent-secret'.
    # If the header is missing, 'x_agent_secret' will be None.
    x_agent_api_key: str | None = Header(default=None),

    # We include the database dependency, as we will use it later.
    db: Session = Depends(get_db)
):
    """
    Receives a list of backup jobs from a Naruto agent, authenticates the agent
    via its unique API key, and saves the jobs to the database associated
    with the correct data source.
    """
    # Step 1: Authenticate the agent using the shared secret.
    if x_agent_api_key is None:
        # If the secret is missing or incorrect, reject the request.
        raise HTTPException(status_code=401, detail="Invalid Agent API Key")
    print(f"HOKAGE: Received {len(jobs)} jobs from a trusted Naruto agent. Trying to Save to Database...")
    data_source = crud.get_data_source_by_api_key(db, api_key=x_agent_api_key)
    # Step 2: Process the data (placeholder for now).
    # This print statement will show up in your 'docker-compose up' log,
    # proving that the data was received successfully.
    print(f"HOKAGE: Received {len(jobs)} jobs from a trusted Naruto agent. Saving to Database...")
    new_jobs = []
    for job_schema in jobs:
        db_job = models.BackupJob(
            data_source_id=data_source.id,
            **job_schema.model_dump()
        )
        new_jobs.append(db_job)

    db.add_all(new_jobs)
    db.commit()

    # Step 3: Send a success response back to the agent.
    return {"status": "ok", "received_jobs": len(jobs)}

@app.get("/api/v1/jobs/", response_model=List[schemas.BackupJob])
def read_backup_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    jobs = crud.get_jobs_by_tenant(db, tenant_id=current_user.tenant_id)
    return jobs

@app.get("/api/v1/jobs/{job_db_id}", response_model=schemas.BackupJob)
def read_job_by_id(
    job_db_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Gets a single backup job by its database ID, ensuring tenant security."""
    job = crud.get_job_by_id_for_tenant(db, job_db_id=job_db_id, tenant_id=current_user.tenant_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def get_job_by_id_for_tenant(db: Session, job_db_id: int, tenant_id: int):
    """Gets a single job, verifying it belongs to the correct tenant."""
    return db.query(models.BackupJob).join(models.DataSource).filter(
        models.BackupJob.id == job_db_id,
        models.DataSource.tenant_id == tenant_id
    ).first()
# Backup Job APIs End

# Assets APIs Start

@app.get("/api/v1/tenant/users", response_model=List[schemas.User])
def read_tenant_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieves a list of all users belonging to the current user's tenant."""
    users = crud.get_users_by_tenant(db, tenant_id=current_user.tenant_id)
    return users

@app.post("/api/v1/ingest/assets", status_code=202)
def ingest_assets_from_agent(
    payload: schemas.AssetIngestPayload,
    x_agent_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Receives a full asset inventory from an agent for a specific hypervisor.
    It performs a full reconciliation (delete then create) for that tenant.
    """
    # 1. Authenticate the agent and get its associated tenant
    if not x_agent_api_key:
        raise HTTPException(status_code=401, detail="Agent API Key is missing")
    data_source = crud.get_data_source_by_api_key(db, api_key=x_agent_api_key)
    if not data_source:
        raise HTTPException(status_code=401, detail="Invalid Agent API Key")
    
    tenant_id = data_source.tenant_id

    try:
        # 2. Reconcile: Delete old assets for this tenant
        crud.delete_assets_by_tenant(db, tenant_id=tenant_id)

        # 3. Create the new assets from the payload
        crud.bulk_create_assets(db, assets=payload.asset_list, tenant_id=tenant_id)
        
        # 4. Commit the transaction
        db.commit()

        return {"status": "ok", "message": f"Successfully reconciled {len(payload.asset_list)} assets for tenant {tenant_id}."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/api/v1/tenant/unprotected-assets", response_model=List[str])
def get_unprotected_assets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Analyzes the stored asset data for the current user's tenant and returns
    a list of assets that are unprotected.
    """
    unprotected_list = crud.get_unprotected_assets_for_tenant(db, tenant_id=current_user.tenant_id)
    return unprotected_list

# Assets APIs End

# Alerts APIs Start

@app.post("/api/v1/ingest/alerts", status_code=202)
def ingest_alerts_from_agent(
    payload: List[schemas.AlertCreate],
    x_agent_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Receives a list of recent alerts from an agent.
    It performs an "upsert" logic, inserting only the new alerts that have not
    been seen before, based on their unique live_feed_id.
    """
    # 1. Authenticate the agent (no change here)
    if not x_agent_api_key:
        raise HTTPException(status_code=401, detail="Agent API Key is missing")
    data_source = crud.get_data_source_by_api_key(db, api_key=x_agent_api_key)
    if not data_source:
        raise HTTPException(status_code=401, detail="Invalid Agent API Key")
    
    tenant_id = data_source.tenant_id

    try:
        # 2. Call the new, intelligent upsert function
        new_alerts_count = crud.upsert_alerts(db=db, alerts=payload, tenant_id=tenant_id)

        return {
            "status": "ok",
            "message": f"Processed {len(payload)} alerts. Created {new_alerts_count} new entries."
        }
    except Exception as e:
        # Rollback in case of a DB error during the upsert
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An internal error occurred during alert ingestion: {e}")
    
@app.get("/api/v1/tenant/alerts/summary", response_model=schemas.AlertSummary)
def get_alerts_summary(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Returns high-level KPI statistics about alerts and jobs for the
    currently logged-in user's tenant.
    """
    summary_data = crud.get_alert_summary_for_tenant(db, tenant_id=current_user.tenant_id)
    return summary_data

@app.post("/api/v1/alerts/{alert_id}/read", response_model=schemas.Alert)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Marks a specific alert as read.
    """
    time.sleep(1.5) 
    updated_alert = crud.mark_alert_as_read(db, alert_id=alert_id, tenant_id=current_user.tenant_id)
    
    if not updated_alert:
        # This error is important for security. It means either the alert doesn't exist,
        # or the user is trying to access an alert that doesn't belong to their tenant.
        raise HTTPException(status_code=404, detail="Alert not found or not accessible")
        
    return updated_alert

@app.get("/api/v1/tenant/alerts", response_model=schemas.AlertsList)
def get_all_alerts(
    alert_name: str | None = None,
    severity: str | None = None, # <-- NEW: Add severity query parameter
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns a list of all alerts for the user's tenant, separated into
    'unread' and 'read' categories.
    """
    alerts_data = crud.get_alerts_for_tenant(db, tenant_id=current_user.tenant_id, alert_name_filter=alert_name, severity_filter=severity)
    return alerts_data

@app.get("/api/v1/tenant/alerts/grouped", response_model=List[schemas.GroupedAlert])
def get_grouped_alerts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Returns a list of alerts that have been intelligently grouped by problem type,
    showing occurrence counts and top affected clients.
    """
    grouped_data = crud.get_grouped_alerts_for_tenant(db, tenant_id=current_user.tenant_id)
    return grouped_data

# Alerts APIs End

# AI Service APIs Start

@app.post("/api/v1/test_ai")
def test_ai_service(request_data: dict):
    """
    A simple endpoint to test the connection to the Perplexity API.
    Expects a JSON body like: {"prompt": "your question here"}
    """
    prompt = request_data.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is missing from request body.")
    
    # This calls the function you just built!
    ai_response = ai_service.get_perplexity_analysis(prompt)
    
    return {"prompt": prompt, "ai_response": ai_response}


@app.get("/api/v1/agent/listen-for-tasks", response_model=schemas.AgentTask, responses={204: {"model": None}})
async def listen_for_agent_tasks(
    request: Request,
    x_agent_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    """(AGENT ONLY) Agent connects here and waits for a task using long polling."""
    if not x_agent_api_key:
        raise HTTPException(status_code=401, detail="Agent API Key is missing")
    data_source = crud.get_data_source_by_api_key(db, api_key=x_agent_api_key)
    if not data_source:
        raise HTTPException(status_code=401, detail="Invalid Agent API Key")
    
    data_source_id = data_source.id
    
    task = crud.get_pending_task_for_agent(db, data_source_id=data_source_id)
    if task:
        crud.update_task_status(db, task_id=task.id, new_status="processing")
        return task

    waiter = asyncio.Future()
    agent_task_channels[data_source_id] = waiter
    
    try:
        # This is the core of the long poll. The code will pause here and wait.
        # It will either be "woken up" by the Future getting a result,
        # or it will be cancelled if the client disconnects.
        await waiter
        
        # If we get here, it means waiter.set_result() was called.
        # The result of the future is the task itself.
        task_to_return = waiter.result()
        return task_to_return

    except asyncio.CancelledError:
        # This block is executed if the client disconnects.
        print(f"Agent {data_source_id} disconnected.")
        # Return a non-standard but informative status code.
        from fastapi.responses import Response
        return Response(status_code=499) # 499 Client Closed Request
    
    finally:
        # CRITICAL: Always clean up the channel for this agent.
        if data_source_id in agent_task_channels:
            del agent_task_channels[data_source_id]


@app.post("/api/v1/jobs/{job_db_id}/analysis-tasks", status_code=202, response_model=schemas.AgentTask)
def create_job_analysis_task(
    job_db_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    job = db.query(models.BackupJob).join(models.DataSource).filter(
        models.BackupJob.id == job_db_id,
        models.DataSource.tenant_id == current_user.tenant_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    payload = {"job_id": job.job_id}
    new_task = crud.create_agent_task(
        db, 
        data_source_id=job.data_source_id,
        task_type="GET_JOB_DETAILS",
        payload=payload
    )
    
    if job.data_source_id in agent_task_channels:
        waiter = agent_task_channels[job.data_source_id]
        updated_task_model = crud.update_task_status(db, task_id=new_task.id, new_status="processing")
        task_schema = schemas.AgentTask.from_orm(updated_task_model)
        waiter.set_result(task_schema)
    
    return new_task

@app.post("/api/v1/agent/tasks/{task_id}/update")
def update_agent_task_status_and_result(
    task_id: int,
    payload: schemas.AgentTaskUpdatePayload,
    x_agent_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    """(AGENT ONLY) The agent calls this to update a task's status and submit its result/error."""
    if not x_agent_api_key:
        raise HTTPException(status_code=401, detail="Agent API Key is missing")
    
    updated_task = crud.update_task_status(
        db, 
        task_id=task_id, 
        new_status=payload.status, 
        result=payload.result
    )
    
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task to update not found.")
        
    return {"status": "ok", "message": f"Status for task {task_id} updated to {payload.status}."}

@app.get("/api/v1/agent-tasks/{task_id}", response_model=schemas.AgentTask)
def get_task_status_and_result(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    (USER-FACING) The main polling endpoint for the analysis workflow.
    """
    task = crud.get_task_by_id(db, task_id=task_id, tenant_id=current_user.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Stage 1: Perform Triage if it hasn't been done yet.
    if task.task_type == "GET_JOB_DETAILS" and task.status == "complete":
        lock_acquired = crud.lock_task_for_triage(db, task=task)
        if lock_acquired:
            print(f"STATE MACHINE: Running Triage for Task #{task.id}")
            triage_result = crud.perform_ai_triage(db, task=task)
            
            task.result["triage_complete"] = True
            task.result["triage_decision"] = triage_result.model_dump()
            
            if triage_result.is_sufficient:
                task.result["ai_analysis"] = triage_result.analysis.model_dump()
                task.status = "finalized"
            else:
                log_fetch_task_model = crud.create_agent_task(
                    db, 
                    data_source_id=task.data_source_id,
                    task_type="GET_SPECIFIC_LOGS",
                    payload={
                        "job_id": task.result.get("job_id"),
                        "logs_to_fetch": triage_result.logs_needed
                    },
                    parent_task_id=task.id
                )
                if task.data_source_id in agent_task_channels:
                    log_fetch_task_schema = schemas.AgentTask.from_orm(log_fetch_task_model)
                    agent_task_channels[task.data_source_id].set_result(log_fetch_task_schema)
            
            flag_modified(task, "result")
            db.commit()
            db.refresh(task)
        else:
            print(f"STATE MACHINE: Triage for Task #{task.id} is already in progress.")

    # Stage 2: Perform Deep Analysis if the child task is complete.
    # We check if the analysis is missing to prevent re-running it.
    if task.status == "trieaging" and not task.result.get("ai_analysis"):
        child_task = crud.get_completed_child_task(db, parent_task_id=task.id)
        if child_task:
            ai_analysis_result = crud.perform_ai_deep_analysis(db, parent_task=task, child_task=child_task)
            
            task.result["ai_analysis"] = ai_analysis_result
            task.status = "finalized"
            flag_modified(task, "result")
            db.commit()
            db.refresh(task)

    return task