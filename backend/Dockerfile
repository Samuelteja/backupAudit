# -----------------------------------------------------------------------------
# Dockerfile for the Backend FastAPI Application
# -----------------------------------------------------------------------------

# --- Stage 1: Build the Application Image ---
# We start with a slim, official Python image. Using a specific version ensures
# that our builds are reproducible and consistent everywhere.
FROM python:3.11-slim

# --- Environment Variables ---
# These are good practices for Python development within Docker.
# 1. Prevents Python from writing .pyc files to disk, which we don't need.
# 2. Ensures Python output (like print statements) is sent straight to the
#    terminal without being buffered, which is better for logging.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Set Working Directory ---
# We create and set our working directory inside the container. All subsequent
# commands (COPY, RUN, CMD) will be relative to this path.
WORKDIR /app

# --- Install Dependencies ---
# This is a critical optimization step. We copy ONLY the requirements file first.
# Docker builds in layers, and it caches each layer. If this file doesn't change
# on a future build, Docker will use the cached layer from the previous build,
# saving a huge amount of time by not reinstalling all dependencies.
COPY ./requirements.txt .

# We run the pip install command to download and install all the Python libraries
# listed in our requirements.txt file.
# --no-cache-dir reduces the final image size.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Copy Application Code ---
# Now that the dependencies are installed and cached, we copy the rest of our
# application's source code into the working directory inside the container.
# This includes main.py and any other Python files you create.
COPY . .

# --- Expose Port ---
# This instruction informs Docker that the container will listen on port 8000 at runtime.
# This is primarily for documentation and doesn't actually publish the port.
# The actual port mapping is done in the docker-compose.yml file.
EXPOSE 8000

# --- Set the Startup Command ---
# This is the final and most important command. It tells Docker what to run
# when a container is started from this image.
#   - uvicorn: The high-performance server that will run our app.
#   - main:app: Tells uvicorn to look for the file `main.py` and run the FastAPI
#               instance variable named `app` inside it.
#   - --host 0.0.0.0: This is crucial. It tells the server to listen on all
#                     available network interfaces inside the container, making it
#                     accessible from outside the container (e.g., from your browser
#                     or the frontend container).
#   - --port 8000: The port the server will listen on, matching our EXPOSE instruction.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]