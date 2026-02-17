# =============================================================================
# DistriPartner Platform - Teams Bot (M365 Agents SDK)
# =============================================================================
# Configures the AgentApplication and message handlers for Teams integration.
# Bridges incoming Teams messages to the DistriPartner workflow engine.
# =============================================================================

import logging
import re
import sys
import traceback

from os import environ
from dotenv import load_dotenv

from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

from .config import BOT_COSMOS_ENDPOINT
from .workflow_state import WorkflowStateItem
from .workflow_manager import WorkflowManager

load_dotenv()

logger = logging.getLogger(__name__)

# ── M365 Agents SDK Configuration ──
agents_sdk_config = load_configuration_from_env(environ)

# Validate required bot credentials
_client_id = environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID", "")
_auth_type = environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__AUTHTYPE", "")
if not _client_id:
    raise SystemExit(
        "\n[ERROR] Bot credentials not configured.\n"
        "Set the following environment variables (or in .env file):\n"
        "  CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID\n"
        "  CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID\n"
        "  CONNECTIONS__SERVICE_CONNECTION__SETTINGS__AUTHTYPE=UserManagedIdentity\n"
        "\nFor local dev with client secret, set AUTHTYPE=ClientSecret and add:\n"
        "  CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET\n"
        "\nSee .env.example for details.\n"
    )

# Storage: use CosmosDB for production, MemoryStorage for local dev
if BOT_COSMOS_ENDPOINT:
    from microsoft_agents.storage.cosmos import CosmosDbStorage
    from .config import BOT_COSMOS_ENDPOINT, BOT_COSMOS_KEY, BOT_COSMOS_DATABASE, BOT_COSMOS_CONTAINER

    STORAGE = CosmosDbStorage(
        endpoint=BOT_COSMOS_ENDPOINT,
        key=BOT_COSMOS_KEY,
        database_name=BOT_COSMOS_DATABASE,
        container_name=BOT_COSMOS_CONTAINER,
    )
    logger.info("Using CosmosDB storage for bot state")
else:
    STORAGE = MemoryStorage()
    logger.warning("Using MemoryStorage (not suitable for production)")

# Auth and adapter
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

# Bot application
AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE,
    adapter=ADAPTER,
    authorization=AUTHORIZATION,
    **agents_sdk_config,
)

# Workflow manager (shared across all conversations)
WORKFLOW_MANAGER = WorkflowManager()


# ── Handlers ──


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    """Welcome message when user starts a conversation with the bot."""
    members_added = context.activity.members_added
    for member in members_added:
        if member.id != context.activity.recipient.id:
            await context.send_activity(
                "Hi! I'm the DistriPartner support assistant. "
                "I can help you with technical support, create incident tickets, "
                "and answer your questions about Azure, Microsoft 365 and Dynamics. "
                "Type /reset to restart the conversation."
            )
    return True


@AGENT_APP.message(re.compile(r"^/reset$", re.IGNORECASE))
async def on_reset(context: TurnContext, state: TurnState):
    """Reset the current workflow session."""
    conversation_id = context.activity.conversation.id
    WORKFLOW_MANAGER.reset_session(conversation_id)

    # Clear stored workflow state
    state.set_value(
        "ConversationState.workflow", WorkflowStateItem()
    )

    await context.send_activity(
        "Conversation reset. You can start a new query."
    )
    return True


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    """
    Main message handler. Routes user messages through the DistriPartner workflow.

    Flow:
    1. Extract authenticated user identity from Teams activity (first turn only)
    2. Retrieve pending_request_id from conversation state (if multi-turn)
    3. Pass message (enriched with user context) to WorkflowManager
    4. Stream workflow events back to Teams
    5. Save new pending_request_id for next turn
    """
    conversation_id = context.activity.conversation.id
    user_input = context.activity.text or ""

    if not user_input.strip():
        return True

    # Show typing indicator
    context.streaming_response.queue_informative_update("Processing your request...")

    # Get stored workflow state
    workflow_state = state.get_value(
        "ConversationState.workflow",
        lambda: WorkflowStateItem(),
        target_cls=WorkflowStateItem,
    )
    pending_request_id = workflow_state.pending_request_id

    # ── Enrich first message with authenticated user identity ──
    # On Teams, from_property contains the user's display name and AAD Object ID.
    # We inject this as a [System Context] block so agents can use it without
    # asking the user for their name or email. On channels without identity
    # (e.g. Web Chat), no context block is added and agents fall back to asking.
    if not pending_request_id:
        from_user = context.activity.from_property
        user_name = getattr(from_user, "name", None) if from_user else None
        user_aad_id = getattr(from_user, "aad_object_id", None) if from_user else None

        tenant_id = None
        channel_data = context.activity.channel_data
        if isinstance(channel_data, dict):
            tenant_info = channel_data.get("tenant", {})
            tenant_id = tenant_info.get("id") if isinstance(tenant_info, dict) else None

        context_lines = []
        if user_name:
            context_lines.append(f"User Display Name: {user_name}")
        if user_aad_id:
            context_lines.append(f"User Entra Object ID: {user_aad_id}")
        if tenant_id:
            context_lines.append(f"Tenant ID: {tenant_id}")

        if context_lines:
            system_context = (
                "[System Context - Authenticated User Identity]\n"
                + "\n".join(context_lines)
                + "\n[End System Context]\n\n"
            )
            user_input = system_context + user_input

    try:
        # Process through workflow
        async for event in WORKFLOW_MANAGER.process_message(
            conversation_id=conversation_id,
            user_input=user_input,
            pending_request_id=pending_request_id,
        ):
            if event.type == "text" and event.text:
                context.streaming_response.queue_text_chunk(event.text)

            elif event.type == "activity" and event.text:
                context.streaming_response.queue_informative_update(event.text)

            elif event.type == "waiting_for_input":
                # Store pending_request_id for next turn
                workflow_state.pending_request_id = event.pending_request_id
                state.set_value("ConversationState.workflow", workflow_state)

            elif event.type == "completed":
                # Workflow finished - clear state
                workflow_state.pending_request_id = None
                state.set_value("ConversationState.workflow", workflow_state)

    except Exception as e:
        logger.exception("Error processing workflow for %s", conversation_id)
        context.streaming_response.queue_text_chunk(
            "An error occurred while processing your request. "
            "Please try again or type /reset to restart."
        )

    await context.streaming_response.end_stream()
    return True


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    """Global error handler."""
    print(f"\n[on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity(
        "The bot encountered an error. Please try again."
    )
