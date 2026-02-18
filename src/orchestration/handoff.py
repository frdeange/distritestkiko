# =============================================================================
# DistriPartner Platform - HandoffBuilder Orchestration
# =============================================================================
# Creates the multi-agent workflow using HandoffBuilder from the Microsoft
# Agent Framework. Replaces the declarative YAML workflow with LLM-driven
# handoff routing.
#
# Architecture:
#   Agent instructions (YAML) → Read at startup
#   Agent creation (Python)   → AzureOpenAIResponsesClient.as_agent()
#   Orchestration (Python)    → HandoffBuilder with directed handoffs
#   Workflow events            → Streamed to WorkflowManager → Bot
#
# Handoff Topology:
#   Orchestrator → [Support, Ticketing]
#   Support      → [Ticketing, Orchestrator]
#   Ticketing    → [DataGatherer, Communication, Orchestrator]
#   DataGatherer → [Ticketing]           (autonomous)
#   Communication → [Orchestrator]       (autonomous)
# =============================================================================

import os
from pathlib import Path

import yaml
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.orchestrations import HandoffBuilder
from azure.core.credentials import TokenCredential

from agents.response_models import (
    CommunicationResponse,
    DataGathererResponse,
    OrchestratorResponse,
    SupportResponse,
    TicketingResponse,
)

INSTRUCTIONS_DIR = Path(__file__).parent.parent / "agents" / "instructions"


def _read_instructions(yaml_filename: str) -> str:
    """Read agent instructions from a YAML instruction file."""
    yaml_path = INSTRUCTIONS_DIR / yaml_filename
    if not yaml_path.exists():
        raise FileNotFoundError(f"Agent instructions not found: {yaml_path}")
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    return config.get("instructions", "")


def create_handoff_workflow(
    credential: TokenCredential, user_identity: str | None = None
):
    """
    Create the HandoffBuilder workflow with all agents.

    Creates agents using AzureOpenAIResponsesClient.as_agent() and wires
    them together with directed handoffs via HandoffBuilder.

    Args:
        credential: Azure credential for authentication
        user_identity: Optional pre-built system context block with
            authenticated user identity. When provided, this is baked into
            Ticketing and DataGatherer agent instructions.

    Returns:
        Configured Workflow instance ready to run
    """
    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

    # ── Create clients — one per model tier for cost optimization ──
    complex_client = AzureOpenAIResponsesClient(
        project_endpoint=project_endpoint,
        deployment_name=os.getenv("MODEL_DEPLOYMENT_COMPLEX", "gpt-4.1"),
        credential=credential,
    )
    standard_client = AzureOpenAIResponsesClient(
        project_endpoint=project_endpoint,
        deployment_name=os.getenv("MODEL_DEPLOYMENT_STANDARD", "gpt-4.1"),
        credential=credential,
    )
    simple_client = AzureOpenAIResponsesClient(
        project_endpoint=project_endpoint,
        deployment_name=os.getenv("MODEL_DEPLOYMENT_SIMPLE", "gpt-4.1"),
        credential=credential,
    )
    mini_client = AzureOpenAIResponsesClient(
        project_endpoint=project_endpoint,
        deployment_name=os.getenv("MODEL_DEPLOYMENT_MINI", "gpt-4.1-mini"),
        credential=credential,
    )

    # ── MCP URLs ──
    learn_url = os.getenv("MCP_LEARN_URL", "https://learn.microsoft.com/api/mcp")
    cosmosdb_url = os.getenv("MCP_COSMOSDB_URL")
    entraid_url = os.getenv("MCP_ENTRAID_URL")
    email_url = os.getenv("MCP_EMAIL_URL")

    # ── Build agent tools ──

    # Support tools: Microsoft Learn MCP
    support_tools = []
    if learn_url:
        support_tools.append(
            simple_client.get_mcp_tool(
                name="Microsoft Learn MCP",
                url=learn_url,
                approval_mode="never_require",
            )
        )

    # Ticketing tools: CosmosDB for ticket storage
    ticketing_tools = []
    if cosmosdb_url:
        ticketing_tools.append(
            simple_client.get_mcp_tool(
                name="cosmosdb_tools",
                url=cosmosdb_url,
                allowed_tools=[
                    "resourcegraph_query",
                    "cosmos_item_upsert",
                    "cosmos_item_query",
                    "cosmos_item_get",
                ],
                approval_mode="never_require",
            )
        )

    # DataGatherer tools: EntraID + CosmosDB
    datagatherer_tools = []
    if entraid_url:
        datagatherer_tools.append(
            mini_client.get_mcp_tool(
                name="entraid_tools",
                url=entraid_url,
                allowed_tools=[
                    "entraid_user_get",
                    "entraid_user_manager",
                ],
                approval_mode="never_require",
            )
        )
    if cosmosdb_url:
        datagatherer_tools.append(
            mini_client.get_mcp_tool(
                name="cosmosdb_tools",
                url=cosmosdb_url,
                allowed_tools=[
                    "resourcegraph_query",
                    "cosmos_item_query",
                ],
                approval_mode="never_require",
            )
        )

    # Communication tools: Email MCP
    communication_tools = []
    if email_url:
        communication_tools.append(
            mini_client.get_mcp_tool(
                name="email_tools",
                url=email_url,
                allowed_tools=[
                    "communication_email_send",
                    "communication_email_status",
                ],
                approval_mode="never_require",
            )
        )

    # ── Build agent instructions with user identity injection ──
    ticketing_instructions = _read_instructions("ticketing.yaml")
    if user_identity:
        ticketing_instructions += (
            "\n\n## Pre-loaded Authenticated User Identity\n"
            "The following identity was extracted from the authenticated Teams "
            "session. The user IS authenticated — do NOT ask for their name "
            "or email. Use the GatheredData from the DataGatherer agent to "
            "fill in the Customer Information section of the ticket.\n\n"
            f"{user_identity}\n\n"
            "Use the User Display Name to greet the user by name."
        )

    datagatherer_instructions = _read_instructions("datagatherer.yaml")
    if user_identity:
        datagatherer_instructions += (
            "\n\n## Pre-loaded Authenticated User Identity\n"
            "The following identity was extracted from the authenticated Teams "
            "session and Bot Connector API. This data is ALREADY VERIFIED — "
            "the name and email are real, cross-tenant values.\n\n"
            f"{user_identity}\n\n"
            "## Instructions\n"
            "1. The basic identity (name, email) above is ALREADY AVAILABLE. "
            "Use it directly in your response — do NOT set these to null.\n"
            "2. You MAY call the `entraid_user_get` tool to ENRICH the profile "
            "with additional fields (department, jobTitle, organization, manager, "
            "groups, licenses). This is OPTIONAL — if the tool fails (e.g. "
            "cross-tenant user), return success=true with the data you already "
            "have from the system context above.\n"
            "3. Map the system context fields to the output schema: "
            "User Email → email and userPrincipalName, "
            "User Display Name → displayName, "
            "First Name → firstName, Last Name → lastName, "
            "User Entra Object ID → userId."
        )

    # ── Create agents ──
    orchestrator = mini_client.as_agent(
        name="Orchestrator",
        instructions=_read_instructions("orchestrator.yaml"),
        default_options={"response_format": OrchestratorResponse},
    )

    support = simple_client.as_agent(
        name="Support",
        instructions=_read_instructions("support.yaml"),
        tools=support_tools or None,
        default_options={"response_format": SupportResponse},
    )

    ticketing = simple_client.as_agent(
        name="Ticketing",
        instructions=ticketing_instructions,
        tools=ticketing_tools or None,
        default_options={"response_format": TicketingResponse},
    )

    datagatherer = mini_client.as_agent(
        name="DataGatherer",
        instructions=datagatherer_instructions,
        tools=datagatherer_tools or None,
        default_options={"response_format": DataGathererResponse},
    )

    communication = mini_client.as_agent(
        name="Communication",
        instructions=_read_instructions("communication.yaml"),
        tools=communication_tools or None,
        default_options={"response_format": CommunicationResponse},
    )

    # ── Build HandoffBuilder workflow ──
    builder = HandoffBuilder(
        name="DistriPartnerWorkflow",
        participants=[orchestrator, support, ticketing, datagatherer, communication],
        description="DistriPartner multi-agent support platform",
    )

    # Directed handoffs — each agent can only hand off to specific targets
    builder.add_handoff(
        source=orchestrator,
        targets=[support, ticketing],
        description="Route user to Support for technical issues or Ticketing for case creation",
    )
    builder.add_handoff(
        source=support,
        targets=[ticketing, orchestrator],
        description="Escalate unresolved issues to Ticketing or return to Orchestrator when resolved",
    )
    builder.add_handoff(
        source=ticketing,
        targets=[datagatherer, communication, orchestrator],
        description="Request data enrichment, send email notification, or complete ticket flow",
    )
    builder.add_handoff(
        source=datagatherer,
        targets=[ticketing],
        description="Return gathered user profile and subscription data to Ticketing",
    )
    builder.add_handoff(
        source=communication,
        targets=[orchestrator],
        description="Return to Orchestrator after sending email notification",
    )

    # Start with Orchestrator
    builder.with_start_agent(orchestrator)

    # DataGatherer and Communication run autonomously (no user interaction)
    builder.with_autonomous_mode(agents=[datagatherer, communication])

    # Build the workflow
    workflow = builder.build()

    # Log loaded agents
    print(f"\033[36mHandoffBuilder workflow created with agents: "
          f"{', '.join(a.name for a in [orchestrator, support, ticketing, datagatherer, communication])}\033[0m")

    return workflow
