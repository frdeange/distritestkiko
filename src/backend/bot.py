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
from .cosmos_store import CosmosProfileStore, CosmosHistoryStore
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
    from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
    from microsoft_agents.storage.cosmos import CosmosDBStorage, CosmosDBStorageConfig
    from .config import BOT_COSMOS_DATABASE, BOT_COSMOS_CONTAINER

    _msi_client_id = environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID", "")
    _cosmos_config = CosmosDBStorageConfig(
        url=BOT_COSMOS_ENDPOINT,
        credential=AsyncDefaultAzureCredential(
            managed_identity_client_id=_msi_client_id or None
        ),
        database_id=BOT_COSMOS_DATABASE,
        container_id=BOT_COSMOS_CONTAINER,
    )
    STORAGE = CosmosDBStorage(_cosmos_config)
    logger.info("Using CosmosDB storage for bot state (database=%s, container=%s)", BOT_COSMOS_DATABASE, BOT_COSMOS_CONTAINER)
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

# CosmosDB custom stores (profile cache + conversation history)
PROFILE_STORE = CosmosProfileStore() if BOT_COSMOS_ENDPOINT else None
HISTORY_STORE = CosmosHistoryStore() if BOT_COSMOS_ENDPOINT else None


# ── Helpers ──


async def _resolve_user_identity(context: TurnContext) -> tuple[dict, str]:
    """
    Resolve full user identity for the current turn.

    Strategy:
    1. Extract basic fields from from_property (always available)
    2. Check CosmosDB profile cache (by aad_object_id)
    3. If cache miss → call Bot Connector get_conversation_member (cross-tenant)
    4. Cache the result in CosmosDB for future conversations

    Returns:
        (profile_dict, system_context_block)
    """
    from_user = context.activity.from_property
    user_name = getattr(from_user, "name", None) if from_user else None
    user_aad_id = getattr(from_user, "aad_object_id", None) if from_user else None
    user_teams_id = getattr(from_user, "id", None) if from_user else None
    user_tenant_id = getattr(from_user, "tenant_id", None) if from_user else None

    # Fallback: tenant_id from channel_data (older SDK versions)
    if not user_tenant_id:
        channel_data = context.activity.channel_data
        if isinstance(channel_data, dict):
            tenant_info = channel_data.get("tenant", {})
            user_tenant_id = tenant_info.get("id") if isinstance(tenant_info, dict) else None

    # Start with what we know from from_property
    profile = {
        "displayName": user_name,
        "aadObjectId": user_aad_id,
        "tenantId": user_tenant_id,
    }

    # ── Try CosmosDB cache first ──
    cached_profile = None
    if PROFILE_STORE and user_aad_id:
        cached_profile = await PROFILE_STORE.get_profile(user_aad_id)

    if cached_profile:
        # Cache hit — use stored data
        profile.update({
            "email": cached_profile.get("email"),
            "userPrincipalName": cached_profile.get("userPrincipalName"),
            "givenName": cached_profile.get("givenName"),
            "surname": cached_profile.get("surname"),
            "displayName": cached_profile.get("displayName") or user_name,
            "tenantId": cached_profile.get("tenantId") or user_tenant_id,
        })
    else:
        # ── Cache miss → call Bot Connector get_member API ──
        try:
            member = await _call_get_member(context, user_teams_id)
            if member:
                profile.update({
                    "email": getattr(member, "email", None),
                    "userPrincipalName": getattr(member, "user_principal_name", None),
                    "givenName": getattr(member, "given_name", None),
                    "surname": getattr(member, "surname", None),
                    "displayName": getattr(member, "name", None) or user_name,
                    "tenantId": getattr(member, "tenant_id", None) or user_tenant_id,
                })
                logger.info(
                    "get_member returned email=%s for user %s",
                    profile.get("email"), user_aad_id,
                )

                # Cache in CosmosDB for future conversations
                if PROFILE_STORE and user_aad_id:
                    await PROFILE_STORE.upsert_profile(user_aad_id, {
                        "email": profile.get("email"),
                        "userPrincipalName": profile.get("userPrincipalName"),
                        "givenName": profile.get("givenName"),
                        "surname": profile.get("surname"),
                        "displayName": profile.get("displayName"),
                        "tenantId": profile.get("tenantId"),
                        "source": "get_member",
                    })
        except Exception as e:
            logger.warning("get_member failed, continuing with from_property data: %s", e)

    # ── Build system context block ──
    context_lines = []
    if profile.get("displayName"):
        context_lines.append(f"User Display Name: {profile['displayName']}")
    if profile.get("email"):
        context_lines.append(f"User Email: {profile['email']}")
    elif profile.get("userPrincipalName"):
        context_lines.append(f"User Email: {profile['userPrincipalName']}")
    if profile.get("givenName"):
        context_lines.append(f"First Name: {profile['givenName']}")
    if profile.get("surname"):
        context_lines.append(f"Last Name: {profile['surname']}")
    if user_aad_id:
        context_lines.append(f"User Entra Object ID: {user_aad_id}")
    if profile.get("tenantId"):
        context_lines.append(f"Tenant ID: {profile['tenantId']}")

    system_context = ""
    if context_lines:
        system_context = (
            "[System Context - Authenticated User Identity]\n"
            + "\n".join(context_lines)
            + "\n[End System Context]"
        )

    return profile, system_context


async def _call_get_member(context: TurnContext, user_teams_id: str):
    """
    Call Bot Connector get_conversation_member to get email cross-tenant.

    In streaming mode, ConnectorClient is NOT in turn_state. We create one
    manually via ChannelServiceClientFactory (always available).
    """
    connector_client = context.turn_state.get("ConnectorClient")

    if not connector_client:
        # Streaming mode — create connector client via factory
        factory = context.turn_state.get("ChannelServiceClientFactory")
        identity = context.turn_state.get("AgentIdentity")
        oauth_scope = context.turn_state.get(
            "Microsoft.Agents.Builder.ChannelAdapter.OAuthScope"
        )

        if not factory or not identity:
            logger.warning("Cannot create ConnectorClient — factory or identity missing from turn_state")
            return None

        connector_client = await factory.create_connector_client(
            context,
            identity,
            context.activity.service_url,
            oauth_scope or "",
        )

    try:
        member = await connector_client.get_conversation_member(
            conversation_id=context.activity.conversation.id,
            user_id=user_teams_id,
        )
        return member
    finally:
        # Close if we created it ourselves (not from turn_state)
        if not context.turn_state.get("ConnectorClient"):
            try:
                await connector_client.close()
            except Exception:
                pass


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
    1. Resolve user identity (cache → get_member → from_property fallback)
    2. Log user message to conversation history
    3. Pass message (enriched with user context) to WorkflowManager
    4. Stream workflow events back to Teams
    5. Log bot response to conversation history
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

    # ── Resolve user identity (first message only) ──
    user_aad_id = None
    if not workflow_state.user_identity:
        profile, system_context = await _resolve_user_identity(context)
        user_aad_id = profile.get("aadObjectId")

        if system_context:
            workflow_state.user_identity = system_context
            state.set_value("ConversationState.workflow", workflow_state)
            logger.info(
                "Identity resolved for %s: email=%s aad_id=%s",
                context.activity.channel_id,
                profile.get("email", "N/A"),
                user_aad_id,
            )
    else:
        # Extract aad_id from from_property for history logging
        from_user = context.activity.from_property
        user_aad_id = getattr(from_user, "aad_object_id", None) if from_user else None

    # ── Log user message to history ──
    if HISTORY_STORE:
        await HISTORY_STORE.add_message(
            conversation_id=conversation_id,
            user_id=user_aad_id,
            role="user",
            text=user_input,
        )

    # Prepend stored identity to every message
    enriched_input = user_input
    if workflow_state.user_identity:
        enriched_input = workflow_state.user_identity + "\n\nUser Message: " + user_input

    # ── Process through workflow ──
    response_chunks = []
    try:
        async for event in WORKFLOW_MANAGER.process_message(
            conversation_id=conversation_id,
            user_input=enriched_input,
            pending_request_id=pending_request_id,
            user_identity=workflow_state.user_identity,
        ):
            if event.type == "text" and event.text:
                context.streaming_response.queue_text_chunk(event.text)
                response_chunks.append(event.text)

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
        error_msg = (
            "An error occurred while processing your request. "
            "Please try again or type /reset to restart."
        )
        context.streaming_response.queue_text_chunk(error_msg)
        response_chunks.append(error_msg)

    # ── Log bot response to history ──
    if HISTORY_STORE and response_chunks:
        await HISTORY_STORE.add_message(
            conversation_id=conversation_id,
            user_id=user_aad_id,
            role="assistant",
            text="".join(response_chunks),
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
