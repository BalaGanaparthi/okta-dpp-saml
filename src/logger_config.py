"""
Logging configuration for Device Posture Provider
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(app_name='okta-dpp', log_level=None):
    """
    Configure logging for the application

    Args:
        app_name: Name of the application for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Determine log level from environment or default
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Convert string to logging level
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = os.getenv('LOG_DIR', 'logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            # If we can't create logs directory (e.g., in Railway), log to stdout only
            log_dir = None

    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log directory is available)
    if log_dir:
        try:
            # Application log file
            app_log_file = os.path.join(log_dir, f'{app_name}.log')
            file_handler = RotatingFileHandler(
                app_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)

            # Error log file (ERROR and above only)
            error_log_file = os.path.join(log_dir, f'{app_name}-error.log')
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(error_handler)

            root_logger.info(f"Logging initialized. Log files: {app_log_file}, {error_log_file}")
        except Exception as e:
            root_logger.warning(f"Could not set up file logging: {e}")
    else:
        root_logger.info("Logging initialized (console only)")

    # Set specific loggers to appropriate levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Flask's logger
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return root_logger


def get_logger(name):
    """
    Get a logger instance

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience functions for structured logging
def log_request(logger, method, path, status_code=None, duration_ms=None):
    """Log HTTP request"""
    msg = f"{method} {path}"
    if status_code:
        msg += f" - {status_code}"
    if duration_ms:
        msg += f" ({duration_ms:.2f}ms)"
    logger.info(msg)


def log_saml_event(logger, event_type, request_id=None, user=None, issuer=None, details=None):
    """Log SAML-related events"""
    msg = f"SAML {event_type}"
    if request_id:
        msg += f" [ID: {request_id[:8]}...]"
    if user:
        msg += f" [User: {user}]"
    if issuer:
        msg += f" [Issuer: {issuer.split('/')[-1] if '/' in issuer else issuer}]"
    if details:
        msg += f" - {details}"
    logger.info(msg)


def log_device_check(logger, device_id, user, is_managed, is_compliant, result):
    """Log device posture check"""
    status = "PASS" if result else "FAIL"
    logger.info(
        f"Device Check [{status}] - Device: {device_id}, User: {user}, "
        f"Managed: {is_managed}, Compliant: {is_compliant}"
    )


def log_error(logger, error, context=None):
    """Log error with context"""
    msg = f"Error: {str(error)}"
    if context:
        msg += f" | Context: {context}"
    logger.error(msg, exc_info=True)


def log_security_event(logger, event_type, details, severity='INFO'):
    """Log security-related events"""
    msg = f"SECURITY [{event_type}] - {details}"
    if severity == 'CRITICAL':
        logger.critical(msg)
    elif severity == 'ERROR':
        logger.error(msg)
    elif severity == 'WARNING':
        logger.warning(msg)
    else:
        logger.info(msg)
