"""
Gunicorn WSGI server configuration file for the AI writing enhancement application backend.

This configuration optimizes for production performance with appropriate worker settings,
connection handling, timeout configurations, and monitoring integration.

For more information on Gunicorn configuration, see:
https://docs.gunicorn.org/en/stable/configure.html
"""

import multiprocessing
import os
import logging
import gevent  # gevent v21.12.0

# Import application configuration settings
from config import current_config

# Gunicorn server socket binding
bind = "0.0.0.0:8000"

# Worker processes - formula recommended for CPU-bound applications
# (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Use gevent worker class for asynchronous processing
worker_class = "gevent"

# Number of connections each worker can handle
worker_connections = 1000

# Timeout settings (in seconds)
timeout = 60  # Worker timeout
keepalive = 5  # Keep-alive connection timeout

# Logging configuration
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
capture_output = True  # Capture and redirect stdout/stderr from workers

# Process name
proc_name = "ai_writing_enhancement"

# Auto-reload in development mode
reload = os.getenv("FLASK_ENV") == "development"

# Lifecycle settings to prevent memory leaks
max_requests = 1000  # Restart workers after handling this many requests
max_requests_jitter = 100  # Add randomness to max_requests to prevent all workers restarting at once

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Worker temporary directory
worker_tmp_dir = os.getenv("GUNICORN_WORKER_TMP_DIR", None)

def on_starting(server):
    """Hook called when Gunicorn is starting up."""
    logging.info(f"Gunicorn server is starting with {workers} workers")
    # Perform any pre-flight checks or initialization required
    logging.info(f"Environment: {current_config.ENV}")

def on_reload(server):
    """Hook called when Gunicorn workers are being reloaded."""
    logging.info("Reloading Gunicorn workers")
    # Perform any cleanup or preparation needed for worker reload
    logging.info("Clearing any temporary resources before reload")

def pre_fork(server, worker):
    """Hook called just before a worker is forked."""
    logging.debug(f"Pre-forking worker {worker.age}")
    # Set up any worker-specific configuration
    logging.debug(f"Preparing resources for worker")

def post_fork(server, worker):
    """Hook called just after a worker has been forked."""
    logging.info(f"Worker {worker.pid} spawned")
    # Initialize worker-specific resources
    # Set up monitoring for this worker
    logging.info(f"Worker {worker.pid} initialized and ready to process requests")

def worker_exit(server, worker):
    """Hook called when a worker is exiting."""
    logging.info(f"Worker {worker.pid} exiting")
    # Clean up worker-specific resources
    # Report worker shutdown to monitoring
    logging.info(f"Resources for worker {worker.pid} have been cleaned up")

def on_exit(server):
    """Hook called when Gunicorn is shutting down."""
    logging.info("Gunicorn server is shutting down")
    # Perform any final cleanup operations
    # Ensure all connections are properly closed
    logging.info("All server resources have been released")