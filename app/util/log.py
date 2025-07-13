import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

# Import configuration
from .log_config import get_logging_config, get_module_log_level

# Configuration constants
DEFAULT_LOG_LEVEL = logging.INFO
DEBUG_LOG_LEVEL = logging.DEBUG
LOG_DIR = Path("./logs")
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5  # Keep 5 backup files

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)


# Custom formatter with more context
class DetailedFormatter(logging.Formatter):
    """Custom formatter with colored output for console and detailed file logging."""

    def __init__(self, include_color: bool = False):
        self.include_color = include_color
        super().__init__()

    def format(self, record):
        # Add extra context
        if not hasattr(record, "funcName"):
            record.funcName = "unknown"
        if not hasattr(record, "lineno"):
            record.lineno = 0

        # Different formats for different log levels
        if record.levelno >= logging.ERROR:
            fmt = "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
        elif record.levelno >= logging.WARNING:
            fmt = "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
        else:
            fmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

        # Add colors for console output
        if self.include_color:
            colors = {
                "DEBUG": "\033[36m",  # Cyan
                "INFO": "\033[32m",  # Green
                "WARNING": "\033[33m",  # Yellow
                "ERROR": "\033[31m",  # Red
                "CRITICAL": "\033[35m",  # Magenta
                "RESET": "\033[0m",  # Reset
            }

            level_color = colors.get(record.levelname, "")
            reset_color = colors["RESET"]
            fmt = f"{level_color}{fmt}{reset_color}"

        formatter = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class LoggerSetup:
    """Centralized logger setup and configuration."""

    _loggers = {}
    _configured = False

    @classmethod
    def setup_logging(
        cls, log_level: Optional[str] = None, enable_console: bool = True
    ):
        """
        Setup logging configuration with file rotation and console output.

        Args:
            log_level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            enable_console: Whether to enable console logging
        """
        if cls._configured:
            return

        # Determine log level
        level = getattr(
            logging,
            (log_level or os.getenv("LOG_LEVEL", "INFO")).upper(),
            DEFAULT_LOG_LEVEL,
        )

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove any existing handlers
        root_logger.handlers.clear()

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=LOG_DIR / "app.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(DetailedFormatter(include_color=False))
        root_logger.addHandler(file_handler)

        # Separate error log file
        error_handler = logging.handlers.RotatingFileHandler(
            filename=LOG_DIR / "error.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(DetailedFormatter(include_color=False))
        root_logger.addHandler(error_handler)

        # Console handler (optional)
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            # Only use colors on Unix-like systems or Windows with colorama
            use_colors = os.name != "nt" or _check_colorama_available()
            console_handler.setFormatter(DetailedFormatter(include_color=use_colors))
            root_logger.addHandler(console_handler)

        # Prevent duplicate logs from propagating to root
        logging.getLogger().propagate = False

        cls._configured = True

        # Log the initialization
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized with level: {logging.getLevelName(level)}")
        logger.info(f"Log files: {LOG_DIR / 'app.log'}, {LOG_DIR / 'error.log'}")


def _check_colorama_available() -> bool:
    """Check if colorama is available for Windows colored output."""
    try:
        import colorama

        colorama.init()
        return True
    except ImportError:
        return False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with proper configuration.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance
    """
    # Ensure logging is configured
    if not LoggerSetup._configured:
        LoggerSetup.setup_logging()

    # Return cached logger or create new one
    if name not in LoggerSetup._loggers:
        logger = logging.getLogger(name)

        # Set module-specific log level
        module_level = get_module_log_level(name)
        logger.setLevel(getattr(logging, module_level.upper(), logging.INFO))

        LoggerSetup._loggers[name] = logger

    return LoggerSetup._loggers[name]


def configure_logging(
    log_level: str = None, enable_console: bool = None, environment: str = None
):
    """
    Configure logging for the application using environment-based settings.

    Args:
        log_level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        enable_console: Whether to enable console logging
        environment: Environment name ('development', 'production', 'testing')
    """
    # Get configuration based on environment
    config = get_logging_config(environment)

    # Override with provided parameters
    final_log_level = log_level or config["log_level"]
    final_enable_console = (
        enable_console if enable_console is not None else config["enable_console"]
    )

    LoggerSetup.setup_logging(final_log_level, final_enable_console)


# Context managers for temporary log level changes
class TemporaryLogLevel:
    """Context manager for temporarily changing log level."""

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.original_level = None

    def __enter__(self):
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)


# Utility functions for structured logging
def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """Log function calls with parameters."""
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


def log_performance(logger: logging.Logger, operation: str, duration: float):
    """Log performance metrics."""
    logger.info(f"Performance: {operation} completed in {duration:.3f}s")


def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """Log exceptions with context."""
    context_msg = f" in {context}" if context else ""
    logger.exception(f"Exception{context_msg}: {str(exception)}")


# Initialize logging on module import
configure_logging()
