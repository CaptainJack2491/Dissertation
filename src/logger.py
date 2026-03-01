"""
Centralized logging module for the experiment framework.
Provides configurable debug levels:
  - Level 1: CRITICAL only
  - Level 2: WARNING + CRITICAL
  - Level 3: INFO + WARNING + CRITICAL
  - Level 4: DEBUG + INFO + WARNING + CRITICAL (full API calls, reasoning, VFS)
"""
import logging
import os
import sys
from typing import Optional

# Custom level names
LEVEL_NAMES = {
    logging.CRITICAL: "CRITICAL",
    logging.WARNING: "WARN",
    logging.INFO: "INFO",
    logging.DEBUG: "DEBUG",
}

# Define DEBUG level (10) below INFO (20)
DEBUG_LEVEL = logging.DEBUG  # 10


def setup_logger(
    name: str = "experiment",
    level: int = 3,
    log_format: str = "[{level}] {message}",
    output: str = "console",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Logger name
        level: Debug level (1-4)
        log_format: Format string for log messages
        output: Output destination - "console", "file", or "both"
        log_file: Path to log file (required if output is "file" or "both")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear any existing handlers
    logger.handlers.clear()

    # Determine actual logging level based on debug level
    # Level 1: CRITICAL only (50)
    # Level 2: WARNING (30) + CRITICAL (50)
    # Level 3: INFO (20) + WARNING (30) + CRITICAL (50)
    # Level 4: DEBUG (10) + INFO + WARNING + CRITICAL (full API calls, reasoning, VFS)
    if level >= 4:
        actual_level = logging.DEBUG
    elif level >= 3:
        actual_level = logging.INFO
    elif level >= 2:
        actual_level = logging.WARNING
    else:
        actual_level = logging.CRITICAL

    logger.setLevel(actual_level)

    # Create formatter
    class CustomFormatter(logging.Formatter):
        """Custom formatter that uses our format string."""

        def format(self, record):
            # Use our custom level names
            levelname = record.levelname
            if record.levelno == logging.CRITICAL:
                levelname = "CRITICAL"
            elif record.levelno == logging.WARNING:
                levelname = "WARN"
            elif record.levelno == logging.INFO:
                levelname = "INFO"
            elif record.levelno == logging.DEBUG:
                levelname = "DEBUG"

            msg = record.getMessage()
            return log_format.format(level=levelname, message=msg)

    formatter = CustomFormatter()

    # For level 4 (DEBUG), automatically enable both console and file output
    if level >= 4 and output == "console":
        output = "both"
        if not log_file:
            log_file = "logs/experiment.log"

    # Console handler
    if output in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if output in ("file", "both"):
        if not log_file:
            raise ValueError("log_file must be specified when output is 'file' or 'both'")

        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "experiment") -> logging.Logger:
    """
    Get an existing logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
