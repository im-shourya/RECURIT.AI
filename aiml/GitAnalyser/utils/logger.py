"""
Structured logging configuration for the application.
Provides consistent, JSON-formatted logs for production monitoring.
"""
import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime


class StructuredLogger:
    """Structured logger that outputs JSON-formatted logs."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def _log(self, level: str, message: str, **kwargs: Any):
        """Internal logging method."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        
        if level == "INFO":
            self.logger.info(json.dumps(log_data))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_data))
        elif level == "ERROR":
            self.logger.error(json.dumps(log_data))
        elif level == "DEBUG":
            self.logger.debug(json.dumps(log_data))
    
    def info(self, message: str, **kwargs: Any):
        """Log info message."""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any):
        """Log warning message."""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs: Any):
        """Log error message."""
        self._log("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any):
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        return record.getMessage()


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
