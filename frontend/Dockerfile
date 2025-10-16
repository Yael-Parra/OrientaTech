# ===================================
# FRONTEND DOCKERFILE (PRODUCTION)
# Multi-stage build for React + Vite
# ===================================

# ===================================
# STAGE 1: BUILD
# ===================================
FROM node:20-slim AS builder

# Install system dependencies for Ubuntu
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including dev dependencies for build)    
# Try npm ci first, fallback to npm install if it fails
RUN npm ci --verbose --no-audit --no-fund || (echo "npm ci failed, trying npm install..." && npm install --no-audit --no-fund)

# Copy source code
COPY . .

# Build the application
RUN npm run build

# ===================================
# STAGE 2: PRODUCTION
# ===================================
FROM nginx:latest AS production

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Use existing nginx user (already exists in nginx:alpine)
# No need to create nginx user/group as they already exist

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    mkdir -p /var/run && \
    chown -R nginx:nginx /var/run

# Keep running as root to avoid permission issues with nginx
# USER nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
