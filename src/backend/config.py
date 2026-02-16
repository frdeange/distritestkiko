# =============================================================================
# DistriPartner Platform - Backend Configuration
# =============================================================================
# Centralizes configuration loading for the Teams bot backend.
# =============================================================================

import os

from dotenv import load_dotenv

load_dotenv()

# Server
PORT = int(os.getenv("PORT", "3978"))

# Workflow session TTL (seconds) - inactive sessions are cleaned up
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "1800"))  # 30 min

# Cosmos DB for bot conversation state (M365 Agents SDK storage)
BOT_COSMOS_ENDPOINT = os.getenv("BOT_COSMOS_ENDPOINT", "")
BOT_COSMOS_KEY = os.getenv("BOT_COSMOS_KEY", "")
BOT_COSMOS_DATABASE = os.getenv("BOT_COSMOS_DATABASE", "distripartner-bot")
BOT_COSMOS_CONTAINER = os.getenv("BOT_COSMOS_CONTAINER", "bot-state")
