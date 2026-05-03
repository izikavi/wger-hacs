"""Constants for the wger integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "wger"

CONF_URL = "url"
CONF_API_KEY = "api_key"
CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_URL = "https://wger.de"
DEFAULT_VERIFY_SSL = True
DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)

API_PATH = "/api/v2"
