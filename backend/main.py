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
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import List

import database, models, schemas, crud, security

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

origins = [
    "http://localhost",
    "http://localhost:3000", # The origin of our React frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allow the origins listed above
    allow_credentials=True, # Allow cookies to be included in requests (important for auth later)
    allow_methods=["*"],    # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Allow all headers
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Assurance Platform API!"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/users/", response_model=schemas.User)
def signup_new_user_and_tenant(user: schemas.UserCreateWithTenant, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_user_and_tenant(db=db, user_data=user)

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


# --- NEW PROTECTED ENDPOINT ---
#
# The response_model filters the output to match the schemas.User shape.
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

@app.get("/api/v1/tenant/users", response_model=List[schemas.User])
def read_tenant_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_users_by_tenant(db, tenant_id=current_user.tenant_id)

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

# Agent Ingest Endpoint
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

@app.get("/api/v1/jobs/{job_id}", response_model=schemas.BackupJob)
def read_backup_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # We use the CRUD function to get jobs linked to the user's tenant_id
    jobs = crud.get_jobs_by_tenant(db, tenant_id=current_user.tenant_id)
    return jobs