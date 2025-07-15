# main.py

# Import the FastAPI class from the fastapi library
from fastapi import FastAPI

# Create an instance of the FastAPI class.
# This 'app' variable is what uvicorn will look for.
app = FastAPI()

# Define an API endpoint using a decorator.
# This tells FastAPI that any GET request to the root path ("/")
# should be handled by the function below.
@app.get("/")
def read_root():
    """
    This is the root endpoint of the API.
    """
    return {"message": "Welcome to the Assurance Platform API!"}

# Define another endpoint for our health check.
@app.get("/api/v1/health")
def health_check():
    """
    A simple health check endpoint.
    """
    return {"status": "ok"}