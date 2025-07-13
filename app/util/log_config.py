"""
Logging configuration settings.

This module provides configuration options for the logging system.
"""

import os
from typing import Dict, Any

# Environment-based configuration
LOGGING_CONFIG = {
    "development": {
        "log_level": "DEBUG",
        "enable_console": True,
        "log_file_level": "DEBUG",
        "console_level": "INFO",
        "format_style": "detailed",
    },
    "production": {
        "log_level": "INFO",
        "enable_console": False,
        "log_file_level": "INFO",
        "console_level": "WARNING",
        "format_style": "standard",
    },
    "testing": {
        "log_level": "WARNING",
        "enable_console": True,
        "log_file_level": "INFO",
        "console_level": "ERROR",
        "format_style": "minimal",
    },
}


def get_logging_config(environment: str = None) -> Dict[str, Any]:
    """
    Get logging configuration for the specified environment.

    Args:
        environment: Environment name ('development', 'production', 'testing')
                    If None, uses ENVIRONMENT env var or defaults to 'development'

    Returns:
        Dictionary with logging configuration
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()

    config = LOGGING_CONFIG.get(environment, LOGGING_CONFIG["development"])

    # Override with environment variables if they exist
    config = {
        "log_level": os.getenv("LOG_LEVEL", config["log_level"]),
        "enable_console": os.getenv(
            "ENABLE_CONSOLE_LOG", str(config["enable_console"])
        ).lower()
        == "true",
        "log_file_level": os.getenv("LOG_FILE_LEVEL", config["log_file_level"]),
        "console_level": os.getenv("CONSOLE_LOG_LEVEL", config["console_level"]),
        "format_style": os.getenv("LOG_FORMAT_STYLE", config["format_style"]),
    }

    return config


# Logging patterns for different modules
MODULE_LOG_LEVELS = {
    "app.routes": "INFO",
    "app.repositories": "DEBUG",
    "app.util": "INFO",
    "uvicorn": "WARNING",
    "fastapi": "INFO",
}


def get_module_log_level(module_name: str) -> str:
    """
    Get the appropriate log level for a specific module.

    Args:
        module_name: Name of the module

    Returns:
        Log level string
    """
    # Check for exact match first
    if module_name in MODULE_LOG_LEVELS:
        return MODULE_LOG_LEVELS[module_name]

    # Check for partial matches (e.g., 'app.routes.user' matches 'app.routes')
    for pattern, level in MODULE_LOG_LEVELS.items():
        if module_name.startswith(pattern):
            return level

    # Default to INFO if no match found
    return "INFO"
