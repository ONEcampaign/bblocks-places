"""Configuration settings

- Logger
- Paths
- Custom exceptions
- Enums for NotFoundBehavior and MultipleCandidatesBehavior

"""

import logging
from pathlib import Path
from enum import Enum

# Configure Logging
logger = logging.getLogger(__name__)
shell_handler = logging.StreamHandler()  # Create terminal handler
logger.setLevel(logging.INFO)  # Set levels for the logger, shell and file
shell_handler.setLevel(logging.INFO)  # Set levels for the logger, shell and file

# Format the outputs   "%(levelname)s (%(asctime)s): %(message)s"
fmt_file = "%(levelname)s: %(message)s"

# "%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s"
fmt_shell = "%(levelname)s: %(message)s"

shell_formatter = logging.Formatter(fmt_shell)  # Create formatters
shell_handler.setFormatter(shell_formatter)  # Add formatters to handlers
logger.addHandler(shell_handler)  # Add handlers to the logger


class Paths:
    """Configuration for paths"""

    project = Path(__file__).resolve().parent.parent


class DataCommonsAPIError(Exception):
    """Custom exception for Data Commons API errors."""

    pass


class PlaceNotFoundError(Exception):
    """Custom exception when a place is not found or cannot be resolved."""

    pass


class MultipleCandidatesError(Exception):
    """Custom exception there are multiple candidates for a place"""

    pass


class NotFoundBehavior(str, Enum):
    RAISE = "raise"
    IGNORE = "ignore"


class MultipleCandidatesBehavior(str, Enum):
    RAISE = "raise"
    FIRST = "first"
    LAST = "last"
    IGNORE = "ignore"
