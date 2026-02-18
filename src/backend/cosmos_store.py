# =============================================================================
# DistriPartner Platform - CosmosDB Custom Stores
# =============================================================================
# Provides direct CosmosDB persistence for user profiles and conversation
# history. Uses azure.cosmos.aio with DefaultAzureCredential (Managed Identity).
#
# Containers:
#   - user-profiles   (/aadObjectId)  — cached user identity from get_member
#   - conversation-history (/conversationId) — message log with 30-day TTL
# =============================================================================

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

from .config import (
    BOT_COSMOS_ENDPOINT,
    BOT_COSMOS_DATABASE,
    BOT_COSMOS_PROFILES_CONTAINER,
    BOT_COSMOS_HISTORY_CONTAINER,
)

logger = logging.getLogger(__name__)

# ── Singleton CosmosDB connection ──
# Shared across both stores — initialized lazily on first use.

_cosmos_client: Optional[CosmosClient] = None
_database = None


async def _get_database():
    """Get (or create) the shared CosmosDB database reference."""
    global _cosmos_client, _database

    if _database is not None:
        return _database

    if not BOT_COSMOS_ENDPOINT:
        raise RuntimeError(
            "BOT_COSMOS_ENDPOINT is not set — cannot initialize CosmosDB stores"
        )

    import os

    msi_client_id = os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID")
    credential = DefaultAzureCredential(
        managed_identity_client_id=msi_client_id or None
    )
    _cosmos_client = CosmosClient(url=BOT_COSMOS_ENDPOINT, credential=credential)
    _database = _cosmos_client.get_database_client(BOT_COSMOS_DATABASE)
    logger.info(
        "CosmosDB stores initialized (database=%s)", BOT_COSMOS_DATABASE
    )
    return _database


# =============================================================================
# User Profile Store
# =============================================================================


class CosmosProfileStore:
    """
    Caches user profiles in CosmosDB.

    Each profile is keyed by aadObjectId. Data comes from the Bot Connector
    get_member API (cross-tenant) and optionally enriched by EntraID MCP.

    Document schema:
    {
        "id": "<aadObjectId>",
        "aadObjectId": "<aadObjectId>",
        "email": "user@example.com",
        "userPrincipalName": "user@example.com",
        "displayName": "John Doe",
        "givenName": "John",
        "surname": "Doe",
        "tenantId": "<tenant-id>",
        "source": "get_member",
        "createdAt": "2026-02-18T...",
        "updatedAt": "2026-02-18T..."
    }
    """

    def __init__(self):
        self._container = None

    async def _get_container(self):
        if self._container is None:
            db = await _get_database()
            self._container = db.get_container_client(BOT_COSMOS_PROFILES_CONTAINER)
        return self._container

    async def get_profile(self, aad_object_id: str) -> Optional[dict]:
        """Read a cached profile by AAD Object ID. Returns None if not found."""
        try:
            container = await self._get_container()
            item = await container.read_item(
                item=aad_object_id, partition_key=aad_object_id
            )
            logger.info("Profile cache HIT for %s", aad_object_id)
            return item
        except Exception as e:
            # 404 or any other error → cache miss
            error_code = getattr(e, "status_code", None)
            if error_code == 404:
                logger.info("Profile cache MISS for %s", aad_object_id)
            else:
                logger.warning("Profile cache read error for %s: %s", aad_object_id, e)
            return None

    async def upsert_profile(self, aad_object_id: str, profile_data: dict) -> dict:
        """Create or update a user profile in the cache."""
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": aad_object_id,
            "aadObjectId": aad_object_id,
            **profile_data,
            "updatedAt": now,
        }
        # Set createdAt only on first insert
        if "createdAt" not in doc:
            doc["createdAt"] = now

        try:
            container = await self._get_container()
            result = await container.upsert_item(doc)
            logger.info("Profile cached for %s (%s)", aad_object_id, profile_data.get("email", "no-email"))
            return result
        except Exception as e:
            logger.error("Failed to cache profile for %s: %s", aad_object_id, e)
            raise


# =============================================================================
# Conversation History Store
# =============================================================================


class CosmosHistoryStore:
    """
    Logs conversation messages in CosmosDB.

    Each message is stored as a separate document, partitioned by conversationId.
    The container has a 30-day TTL — old messages are automatically purged.

    Document schema:
    {
        "id": "<uuid>",
        "conversationId": "<conversation-id>",
        "userId": "<aad-object-id>",
        "role": "user" | "assistant",
        "text": "message text...",
        "agentName": "Orchestrator",
        "timestamp": "2026-02-18T...",
        "ttl": 2592000
    }
    """

    # 30 days in seconds
    DEFAULT_TTL = 30 * 24 * 60 * 60  # 2_592_000

    def __init__(self):
        self._container = None

    async def _get_container(self):
        if self._container is None:
            db = await _get_database()
            self._container = db.get_container_client(BOT_COSMOS_HISTORY_CONTAINER)
        return self._container

    async def add_message(
        self,
        conversation_id: str,
        user_id: Optional[str],
        role: str,
        text: str,
        agent_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Log a single message (user or assistant) to conversation history."""
        doc = {
            "id": str(uuid4()),
            "conversationId": conversation_id,
            "userId": user_id or "unknown",
            "role": role,
            "text": text[:8000],  # Truncate to avoid massive documents
            "agentName": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ttl": self.DEFAULT_TTL,
        }
        if metadata:
            doc["metadata"] = metadata

        try:
            container = await self._get_container()
            await container.create_item(doc)
        except Exception as e:
            # History logging should never break the bot flow
            logger.warning(
                "Failed to log message to history (conv=%s, role=%s): %s",
                conversation_id, role, e,
            )

    async def get_history(
        self, conversation_id: str, limit: int = 50
    ) -> list[dict]:
        """Read recent messages for a conversation, ordered by timestamp."""
        try:
            container = await self._get_container()
            query = (
                "SELECT c.role, c.text, c.agentName, c.timestamp, c.userId "
                "FROM c WHERE c.conversationId = @convId "
                "ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
            )
            parameters = [
                {"name": "@convId", "value": conversation_id},
                {"name": "@limit", "value": limit},
            ]
            items = []
            async for item in container.query_items(
                query=query,
                parameters=parameters,
                partition_key=conversation_id,
            ):
                items.append(item)
            # Return in chronological order (oldest first)
            items.reverse()
            return items
        except Exception as e:
            logger.warning(
                "Failed to read history for %s: %s", conversation_id, e
            )
            return []
