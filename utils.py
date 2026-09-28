"""
Helper module for logging.

This module provides functions for:
- Setting the directory the log is written to
- Logging messages to a file with a timestamp
"""

import os
from datetime import datetime

# Global variable holding the log directory
_log_dir = None

def set_log_dir(log_dir: str) -> None:
    """Sets the directory used for logging.

    Args:
        log_dir (str): Directory where kohonen-log.txt is written

    Note:
        This function must be called before any logging
        so that messages are written to the correct output folder.
    """
    global _log_dir
    _log_dir = log_dir

def log_message(message: str) -> None:
    """Writes a message to the log file, including a timestamp.

    Args:
        message (str): Message to log

    Note:
        If no log directory is set, logs go to the current directory.
    """
    log_file = os.path.join(_log_dir or ".", "kohonen-log.txt")
    current_time = datetime.now()
    with open(log_file, "a") as log:
        log.write(f"{current_time} {message}\n")
