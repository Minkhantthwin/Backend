# Enhanced Logging System

This enhanced logging system provides enterprise-grade logging capabilities with best practices implemented.

## Features

### 🔧 **Core Features**
- **Multiple Handlers**: Console and file logging with separate error logs
- **Log Rotation**: Automatic log file rotation (10MB max, 5 backups)
- **Colored Console Output**: Better readability with colored log levels
- **Environment-based Configuration**: Different settings for dev/prod/test
- **Module-specific Log Levels**: Fine-grained control per module
- **Structured Logging**: Support for additional context data
- **Performance Logging**: Built-in performance tracking utilities
- **Exception Logging**: Enhanced exception handling with context

### 📁 **Log Files Generated**
- `logs/app.log` - Main application logs (with rotation)
- `logs/error.log` - Error and critical logs only (with rotation)

## Quick Start

### Basic Usage

```python
from app.util.log import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Use different log levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

### Configuration

```python
from app.util.log import configure_logging

# Configure for development
configure_logging(log_level="DEBUG", enable_console=True)

# Configure for production
configure_logging(log_level="INFO", enable_console=False)

# Configure by environment
configure_logging(environment="production")
```

### Advanced Features

#### Structured Logging
```python
logger.info("User login successful", extra={
    'user_id': 12345,
    'username': 'john_doe',
    'ip_address': '192.168.1.100',
    'session_id': 'abc123'
})
```

#### Performance Logging
```python
from app.util.log import log_performance
import time

start_time = time.time()
# ... your code here ...
duration = time.time() - start_time
log_performance(logger, "database_query", duration)
```

#### Function Call Logging
```python
from app.util.log import log_function_call

log_function_call(logger, "process_data", user_id=123, data_type="json")
```

#### Exception Logging
```python
from app.util.log import log_exception

try:
    # risky operation
    result = some_operation()
except Exception as e:
    log_exception(logger, e, "processing user data")
```

#### Temporary Log Level Changes
```python
from app.util.log import TemporaryLogLevel
import logging

# Temporarily change log level for debugging
with TemporaryLogLevel(logger, logging.DEBUG):
    logger.debug("This will be shown even if logger is set to INFO")
```

## Environment Configuration

The system supports three environments with different default settings:

### Development
- Log Level: DEBUG
- Console Output: Enabled
- File Logging: DEBUG level
- Console Logging: INFO level

### Production
- Log Level: INFO
- Console Output: Disabled
- File Logging: INFO level
- Error-only Console: WARNING level

### Testing
- Log Level: WARNING
- Console Output: Enabled
- File Logging: INFO level
- Console Logging: ERROR level

## Environment Variables

Override default settings using environment variables:

```bash
export ENVIRONMENT=production        # Set environment
export LOG_LEVEL=INFO               # Override log level
export ENABLE_CONSOLE_LOG=true      # Enable/disable console
export LOG_FILE_LEVEL=DEBUG         # File logging level
export CONSOLE_LOG_LEVEL=WARNING    # Console logging level
export LOG_FORMAT_STYLE=detailed    # Format style
```

## Module-Specific Configuration

Different modules can have different log levels:

```python
# In log_config.py
MODULE_LOG_LEVELS = {
    'app.routes': 'INFO',
    'app.repositories': 'DEBUG',
    'app.util': 'INFO',
    'uvicorn': 'WARNING',
    'fastapi': 'INFO',
}
```

## Log Format

The enhanced formatter provides different detail levels based on log severity:

### Error/Critical Logs
```
2025-06-29 10:30:45 | app.routes.user | ERROR | user.py:42 | login() | Database connection failed
```

### Warning Logs
```
2025-06-29 10:30:45 | app.routes.user | WARNING | user.py:35 | Rate limit exceeded for user
```

### Info/Debug Logs
```
2025-06-29 10:30:45 | app.routes.user | INFO | User login successful
```

## Best Practices

1. **Use appropriate log levels**:
   - `DEBUG`: Detailed diagnostic info
   - `INFO`: General application flow
   - `WARNING`: Unexpected but handled situations
   - `ERROR`: Error conditions that don't stop the app
   - `CRITICAL`: Serious errors that might stop the app

2. **Include context in log messages**:
   ```python
   logger.info("Processing order", extra={'order_id': order.id, 'user_id': user.id})
   ```

3. **Don't log sensitive information**:
   ```python
   # ❌ Don't do this
   logger.info(f"User login: {username}:{password}")
   
   # ✅ Do this instead
   logger.info("User login attempt", extra={'username': username})
   ```

4. **Use structured logging for important events**:
   ```python
   logger.info("Payment processed", extra={
       'payment_id': payment.id,
       'amount': payment.amount,
       'currency': payment.currency,
       'status': 'success'
   })
   ```

5. **Log exceptions with context**:
   ```python
   try:
       process_payment(payment_data)
   except PaymentError as e:
       log_exception(logger, e, f"payment processing for order {order_id}")
   ```

## Installation

Make sure to install the colorama package for Windows color support:

```bash
pip install colorama
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```
