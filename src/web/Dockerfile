# Build stage
FROM node:18-alpine AS build
# node:18-alpine version 18.17.1

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
# Copying these files separately allows for better layer caching
COPY package.json package-lock.json ./

# Install dependencies
# Using npm ci for more reliable builds and --production to avoid dev dependencies
RUN npm ci --production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:1.23-alpine
# nginx:1.23-alpine version 1.23.4

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx user and group with fixed IDs for better security
# This helps with running as non-root and with consistent file permissions
RUN addgroup -g 101 -S nginx \
    && adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx nginx \
    && chown -R nginx:nginx /usr/share/nginx/html

# Set proper permissions for static files
RUN chmod -R 755 /usr/share/nginx/html

# Switch to non-root user for better security
USER nginx

# Set environment variables
ENV NODE_ENV=production

# Expose port 80 for web traffic
EXPOSE 80

# Start nginx in foreground mode so container doesn't exit
CMD ["nginx", "-g", "daemon off;"]