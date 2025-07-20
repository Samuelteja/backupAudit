# --- Stage 1: Build the React Application with Vite ---
FROM node:18 AS builder
WORKDIR /app
COPY package.json ./
COPY package-lock.json ./
RUN npm ci
COPY . .
# This is the standard build command for Vite
RUN npm run build

# --- Stage 2: Serve the Static Files with Nginx ---
FROM nginx:1.23-alpine

# The only change is here: Vite's output folder is 'dist'
COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80