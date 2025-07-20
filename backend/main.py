# backend/main.py
from dotenv import load_dotenv
load_dotenv()
# --- 1. Core Imports ---
from fastapi import FastAPI, Depends, HTTPException, Header
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

# --- 2. Application-Specific Imports ---
# These come after the core imports.
# We import the modules that contain our database setup and models.
import database, models, schemas, crud, security

# --- 3. Create the FastAPI App Instance ---
# This should be done before you define your routes.
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

# --- 4. Database Dependency ---
# This function is a "dependency" that provides a database session
# to any API endpoint that needs it.
def get_db():
    db = database.SessionLocal()
    try:
        yield db  # Provide the session to the endpoint
    finally:
        db.close() # Close the session after the request is finished

# --- 5. Security Dependency ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    This is a dependency that our protected endpoints will use.
    It decodes the JWT token, validates it, and fetches the user from the database.
    If the token is invalid or the user doesn't exist, it raises a 401 error.
    """
    # Define a standard exception to raise for all authentication errors.
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT. This function checks the signature and expiration time.
        # If either is invalid, it will raise a JWTError.
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        
        # Get the email (which we stored in the 'sub' claim) from the payload.
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        # We can create a Pydantic model of the token data for validation, though it's simple here.
        token_data = schemas.TokenData(email=email)
    except JWTError:
        # If decoding fails for any reason (bad signature, expired), raise the error.
        raise credentials_exception

    # Now that we have the email, fetch the user from the database.
    user = crud.get_user_by_email(db, email=token_data.email)
    
    # If a user with that email doesn't exist in our DB (e.g., they were deleted),
    # this is also an authentication failure.
    if user is None:
        raise credentials_exception
        
    # If all checks pass, return the complete User model object.
    return user

# --- 5. API Endpoints (Routes) ---
# All your API routes are defined below.

@app.get("/")
def read_root():
    """The root endpoint."""
    return {"message": "Welcome to the Assurance Platform API!"}

@app.get("/api/v1/health")
def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}

@app.post("/api/v1/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Create a new user
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_user(db=db, user=user)

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

# Agent Ingest Endpoint
@app.post("/api/v1/injest/jobs")
def injest_backup_jobs(
    # FastAPI will automatically parse the incoming JSON request body
    # into a list of objects that match our BackupJobCreate schema.
    # If the data doesn't match, it will fail with a 422 error.
    jobs: list[schemas.BackupJobCreate],

    # This tells FastAPI to look for a custom HTTP header named 'x-agent-secret'.
    # If the header is missing, 'x_agent_secret' will be None.
    x_agent_secret: str | None = Header(default=None),

    # We include the database dependency, as we will use it later.
    db: Session = Depends(get_db)
):
    """
    Receives a list of backup jobs from a Naruto agent, authenticates the agent,
    and (for now) prints the received data to the log.
    """
    server_secret = os.getenv("AGENT_SHARED_SECRET")
    # Step 1: Authenticate the agent using the shared secret.
    if x_agent_secret != server_secret:
        # If the secret is missing or incorrect, reject the request.
        raise HTTPException(status_code=401, detail="Invalid Agent Secret Key")

    # Step 2: Process the data (placeholder for now).
    # This print statement will show up in your 'docker-compose up' log,
    # proving that the data was received successfully.
    print(f"HOKAGE: Received {len(jobs)} jobs from a trusted Naruto agent.")
    for job in jobs:
        print(f"  - Job ID: {job.job_id}, Status: {job.status}")

    # Step 3: Send a success response back to the agent.
    return {"status": "ok", "received_jobs": len(jobs)}
