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

# Cosmos DB (using DefaultAzureCredential — no access keys)
BOT_COSMOS_ENDPOINT = os.getenv("BOT_COSMOS_ENDPOINT", "")
BOT_COSMOS_DATABASE = os.getenv("BOT_COSMOS_DATABASE", "distripartner-bot")
BOT_COSMOS_CONTAINER = os.getenv("BOT_COSMOS_CONTAINER", "bot-state")
BOT_COSMOS_PROFILES_CONTAINER = os.getenv("BOT_COSMOS_PROFILES_CONTAINER", "user-profiles")
BOT_COSMOS_HISTORY_CONTAINER = os.getenv("BOT_COSMOS_HISTORY_CONTAINER", "conversation-history")
