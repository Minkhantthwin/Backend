"""
Example usage of the improved logging system.

This file demonstrates how to use the enhanced logger with best practices.
"""

from app.util.log import (
    get_logger,
    log_function_call,
    log_performance,
    log_exception,
    TemporaryLogLevel,
)
import time


def example_usage():
    """Demonstrate various logging features."""

    # Get a logger for this module
    logger = get_logger(__name__)

    # Basic logging levels
    logger.debug("This is a debug message")
    logger.info("Application started successfully")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Structured logging examples
    logger.info(
        "User login",
        extra={"user_id": 12345, "username": "john_doe", "ip_address": "192.168.1.100"},
    )

    # Function call logging
    log_function_call(logger, "process_data", user_id=123, data_type="json")

    # Performance logging
    start_time = time.time()
    time.sleep(0.1)  # Simulate work
    duration = time.time() - start_time
    log_performance(logger, "data_processing", duration)

    # Exception logging
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        log_exception(logger, e, "mathematical operation")

    # Temporary log level change
    with TemporaryLogLevel(logger, logging.DEBUG):
        logger.debug("This debug message will be shown even if logger level is INFO")

    logger.info("Example usage completed")


if __name__ == "__main__":
    import logging

    # Configure logging for debug level to see all messages
    from app.util.log import configure_logging

    configure_logging(log_level="DEBUG", enable_console=True)

    example_usage()
