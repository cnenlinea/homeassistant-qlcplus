"""Constants for the QLC+ integration."""

import logging

DOMAIN = "qlcplus"
LOGGER = logging.getLogger(__package__)

# Platforms to be set up
PLATFORMS = ["switch"]

# Default values
DEFAULT_NAME = "QLC+"
DEFAULT_PORT = 9999
DEFAULT_TIMEOUT = 5
DEFAULT_SCAN_INTERVAL = 30

# Service names
SERVICE_SEND_COMMAND = "send_command"
