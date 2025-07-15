# ---------------------------------------------------------------------------
# Dockerfile for the Frontend React Application (using a Multi-Stage Build)
# ---------------------------------------------------------------------------

# --- Stage 1: The "Builder" Stage ---
# We start with a Node.js image to build our React code.
FROM node:18-alpine AS builder

# Set the working directory inside the container.
WORKDIR /app

# Copy the package description files. This is cached for faster builds,
# just like in the backend.
COPY package.json ./
COPY package-lock.json ./

# Install all the project dependencies from package-lock.json.
# 'npm ci' is often preferred in CI/CD for its speed and reliability.
RUN npm ci

# Copy the rest of our application's source code (the 'src' and 'public' folders).
COPY . .

# Run the build script defined in package.json.
# This compiles our React/JS/CSS code into a highly optimized 'build' folder.
RUN npm run build


# --- Stage 2: The "Server" Stage ---
# Now we start fresh with a tiny, super-fast Nginx web server image.
FROM nginx:1.23-alpine

# The only thing we need from the "builder" stage is the final compiled output.
# This line copies the contents of the '/app/build' folder from the 'builder' stage
# into the default web server directory in the Nginx container.
COPY --from=builder /app/build /usr/share/nginx/html

# We need a custom Nginx configuration to make sure client-side routing works.
# We will create this nginx.conf file next.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80, which is the default port for Nginx.
EXPOSE 80

# Nginx automatically starts when the container runs, so we don't need a CMD.