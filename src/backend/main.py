# =============================================================================
# DistriPartner Platform - Bot Entry Point
# =============================================================================
# Starts the Teams bot server.
#
# Usage:
#   python -m src.backend.main
#
# Requirements:
#   - Copy .env.example to .env and fill in bot credentials
#   - Install: pip install -r requirements.txt
# =============================================================================

import logging
import sys

# Configure logging for M365 Agents SDK and DistriPartner
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Set SDK loggers to WARNING to reduce noise
logging.getLogger("microsoft_agents").setLevel(logging.WARNING)
logging.getLogger(__name__).setLevel(logging.INFO)

from .bot import AGENT_APP, CONNECTION_MANAGER
from .start_server import start_server

start_server(
    agent_application=AGENT_APP,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)
