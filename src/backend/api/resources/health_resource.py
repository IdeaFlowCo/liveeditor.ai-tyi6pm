"""
Implements health check endpoints for the AI writing enhancement platform's backend services.
Provides basic and detailed status information about API availability, database connections,
caching services, and external AI service status.
"""

from flask_restful import Resource  # flask_restful 0.3.10
from flask import jsonify, current_app  # flask 2.3.0
import datetime  # standard library
import platform  # standard library
import psutil  # psutil 5.9.0

from ...data.mongodb.connection import is_mongodb_available
from ...data.redis.connection import get_redis_connection, is_redis_available
from ...core.ai.openai_service import OpenAIService
from ...core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

# Global constants
API_VERSION = '1.0.0'
DEFAULT_TIMEOUT = 3


def format_uptime(uptime_seconds):
    """
    Formats system uptime into a human-readable string.
    
    Args:
        uptime_seconds (float): Total uptime in seconds
        
    Returns:
        str: Formatted uptime string (e.g., '3 days, 2 hours, 15 minutes')
    """
    # Convert seconds to days, hours, minutes, seconds
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Build the formatted string
    parts = []
    if days > 0:
        parts.append(f"{int(days)} {'day' if days == 1 else 'days'}")
    if hours > 0:
        parts.append(f"{int(hours)} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        parts.append(f"{int(minutes)} {'minute' if minutes == 1 else 'minutes'}")
    if seconds > 0 and not parts:  # Only include seconds if less than a minute
        parts.append(f"{int(seconds)} {'second' if seconds == 1 else 'seconds'}")
    
    # Join the parts with commas and return
    return ", ".join(parts)


def get_system_info():
    """
    Collects basic system information for detailed health checks.
    
    Returns:
        dict: Dictionary containing system information
    """
    # Get system information
    info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "processor": platform.processor()
    }
    
    # Get uptime information
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.datetime.now().timestamp() - boot_time
        info["uptime"] = format_uptime(uptime_seconds)
        info["boot_time"] = datetime.datetime.fromtimestamp(boot_time).isoformat()
    except Exception as e:
        logger.warning(f"Unable to get system uptime: {str(e)}")
        info["uptime"] = "Unknown"
        info["boot_time"] = "Unknown"
    
    return info


def get_resource_usage():
    """
    Collects system resource usage metrics.
    
    Returns:
        dict: Dictionary containing CPU, memory, and disk usage
    """
    usage = {}
    
    try:
        # Get CPU usage
        usage["cpu"] = {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(),
            "physical_count": psutil.cpu_count(logical=False)
        }
    except Exception as e:
        logger.warning(f"Unable to get CPU usage: {str(e)}")
        usage["cpu"] = {"error": "Unable to get CPU usage"}
    
    try:
        # Get memory usage
        memory = psutil.virtual_memory()
        usage["memory"] = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
    except Exception as e:
        logger.warning(f"Unable to get memory usage: {str(e)}")
        usage["memory"] = {"error": "Unable to get memory usage"}
    
    try:
        # Get disk usage for the root directory
        disk = psutil.disk_usage('/')
        usage["disk"] = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    except Exception as e:
        logger.warning(f"Unable to get disk usage: {str(e)}")
        usage["disk"] = {"error": "Unable to get disk usage"}
    
    return usage


class HealthResource(Resource):
    """Resource providing basic health check endpoint."""
    
    def __init__(self):
        """Initialize the health resource."""
        self.logger = get_logger(__name__)
    
    def get(self):
        """
        Basic health check for liveness probes.
        
        Returns:
            dict: Simple status response with timestamp
        """
        self.logger.info("Health check requested")
        
        # Create a basic response with timestamp
        response = {
            "status": "ok",
            "version": API_VERSION,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        return response, 200


class DetailedHealthResource(Resource):
    """Resource providing detailed health check with dependency status."""
    
    def __init__(self, openai_service):
        """
        Initialize the detailed health resource.
        
        Args:
            openai_service (OpenAIService): OpenAI service instance for checking AI API status
        """
        self._openai_service = openai_service
        self.logger = get_logger(__name__)
    
    def get(self):
        """
        Detailed health check for readiness probes.
        
        Returns:
            dict: Detailed status of all system dependencies
        """
        self.logger.info("Detailed health check requested")
        
        # Check MongoDB connection
        try:
            mongodb_available = is_mongodb_available()
            mongodb_status = "ok" if mongodb_available else "down"
        except Exception as e:
            self.logger.error(f"Error checking MongoDB status: {str(e)}")
            mongodb_status = "error"
            mongodb_available = False
        
        # Check Redis connection
        try:
            redis_client = get_redis_connection()
            redis_available = is_redis_available(redis_client)
            redis_status = "ok" if redis_available else "down"
        except Exception as e:
            self.logger.error(f"Error checking Redis status: {str(e)}")
            redis_status = "error"
            redis_available = False
        
        # Check OpenAI API connection
        try:
            openai_health = self._openai_service.health_check()
            openai_status = openai_health.get("status", "unknown")
            openai_available = openai_status == "ok"
        except Exception as e:
            self.logger.error(f"Error checking OpenAI API status: {str(e)}")
            openai_status = "error"
            openai_available = False
            openai_health = {"error": str(e)}
        
        # Get system information and resource usage
        system_info = get_system_info()
        resource_usage = get_resource_usage()
        
        # Determine overall status
        all_dependencies_ok = mongodb_available and redis_available and openai_available
        overall_status = "ok" if all_dependencies_ok else "degraded"
        status_code = 200 if all_dependencies_ok else 503
        
        # Create detailed response
        response = {
            "status": overall_status,
            "version": API_VERSION,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "dependencies": {
                "mongodb": {
                    "status": mongodb_status,
                    "available": mongodb_available
                },
                "redis": {
                    "status": redis_status,
                    "available": redis_available
                },
                "openai": openai_health
            },
            "system": system_info,
            "resources": resource_usage
        }
        
        return response, status_code


class DependencyHealthResource(Resource):
    """Resource providing health check for a specific dependency."""
    
    def __init__(self, openai_service):
        """
        Initialize the dependency health resource.
        
        Args:
            openai_service (OpenAIService): OpenAI service instance for checking AI API status
        """
        self._openai_service = openai_service
        self.logger = get_logger(__name__)
    
    def get(self, dependency):
        """
        Health check for a specific dependency.
        
        Args:
            dependency (str): Name of the dependency to check ('mongodb', 'redis', 'openai')
            
        Returns:
            dict: Status of the specified dependency
        """
        self.logger.info(f"Health check requested for dependency: {dependency}")
        
        # Validate dependency parameter
        if dependency not in ['mongodb', 'redis', 'openai']:
            return {
                "error": f"Invalid dependency name: {dependency}",
                "valid_dependencies": ['mongodb', 'redis', 'openai']
            }, 400
        
        # Check the requested dependency
        if dependency == 'mongodb':
            try:
                available = is_mongodb_available()
                status = "ok" if available else "down"
                response = {
                    "dependency": "mongodb",
                    "status": status,
                    "available": available,
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                status_code = 200 if available else 503
            except Exception as e:
                self.logger.error(f"Error checking MongoDB status: {str(e)}")
                response = {
                    "dependency": "mongodb",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                status_code = 500
        
        elif dependency == 'redis':
            try:
                redis_client = get_redis_connection()
                available = is_redis_available(redis_client)
                status = "ok" if available else "down"
                response = {
                    "dependency": "redis",
                    "status": status,
                    "available": available,
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                status_code = 200 if available else 503
            except Exception as e:
                self.logger.error(f"Error checking Redis status: {str(e)}")
                response = {
                    "dependency": "redis",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                status_code = 500
        
        elif dependency == 'openai':
            try:
                health_data = self._openai_service.health_check()
                available = health_data.get("status") == "ok"
                response = {
                    "dependency": "openai",
                    "status": health_data.get("status", "unknown"),
                    "available": available,
                    "details": health_data,
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                status_code = 200 if available else 503
            except Exception as e:
                self.logger.error(f"Error checking OpenAI status: {str(e)}")
                response = {
                    "dependency": "openai",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }
                status_code = 500
        
        return response, status_code