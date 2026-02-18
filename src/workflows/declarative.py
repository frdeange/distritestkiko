# =============================================================================
# DistriPartner Platform - Declarative Workflow Runner
# =============================================================================
# Implements the declarative workflow variant using:
# - AzureOpenAIResponsesClient for agent creation (recommended by Microsoft)
# - WorkflowFactory for declarative YAML workflow loading
# - Pydantic models for structured output (response_format)
#
# Architecture:
#   Agent definitions (YAML) → Instructions + tool config (source of truth)
#   Workflow definition (YAML) → Routing, loops, conditions (orchestration)
#   This module (Python) → Glues agents + workflow together, handles I/O
#
# Based on the Microsoft Agent Framework customer_support sample pattern.
# =============================================================================

import asyncio
import json
import os
from pathlib import Path

from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.declarative import (
    AgentExternalInputRequest,
    AgentExternalInputResponse,
    WorkflowFactory,
)
from azure.core.credentials import TokenCredential

import yaml

from .response_models import (
    OrchestratorResponse,
    SupportResponse,
    TicketingResponse,
    ProfilerResponse,
    DataCollectorResponse,
    CommunicationResponse,
)

# ANSI color codes for output formatting
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
RESET = "\033[0m"

AGENTS_DIR = Path(__file__).parent.parent / "agents" / "definitions"
WORKFLOW_YAML = Path(__file__).parent / "workflow.yaml"


def _read_instructions(yaml_filename: str) -> str:
    """Read agent instructions from a YAML definition file."""
    yaml_path = AGENTS_DIR / yaml_filename
    if not yaml_path.exists():
        raise FileNotFoundError(f"Agent definition not found: {yaml_path}")
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    return config.get("instructions", "")


def _resolve_env(value: str) -> str:
    """Resolve =Env.VAR references to environment variable values."""
    if isinstance(value, str) and value.startswith("=Env."):
        return os.getenv(value[5:], "")
    return value


def create_declarative_workflow(
    credential: TokenCredential, user_identity: str | None = None
):
    """
    Create the declarative workflow with all agents.

    Creates agents using AzureOpenAIResponsesClient with project_endpoint
    (recommended by Microsoft for orchestrations). Agent instructions are
    read from the existing YAML definition files.

    Args:
        credential: Azure credential for authentication
        user_identity: Optional pre-built system context block with
            authenticated user identity (name, AAD Object ID, tenant ID).
            When provided, this is baked into Profiler and Ticketing agent
            instructions so they can use it deterministically without
            relying on the Orchestrator LLM to relay it.

    Returns:
        Configured workflow instance ready to run
    """
    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

    # Create clients - one per model tier for cost optimization
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

    # ── Create MCP tools ──
    mcp_tools = {}

    # Microsoft Learn MCP (public, no auth)
    learn_url = os.getenv("MCP_LEARN_URL", "https://learn.microsoft.com/api/mcp")
    if learn_url:
        mcp_tools["learn"] = simple_client.get_mcp_tool(
            name="Microsoft Learn MCP",
            url=learn_url,
            approval_mode="never_require",
        )

    # CosmosDB MCP (authenticated via Foundry connection)
    cosmosdb_url = os.getenv("MCP_COSMOSDB_URL")
    if cosmosdb_url:
        mcp_tools["cosmosdb"] = simple_client.get_mcp_tool(
            name="cosmosdb_tools",
            url=cosmosdb_url,
            approval_mode="never_require",
        )

    # EntraID MCP (authenticated via Foundry connection)
    entraid_url = os.getenv("MCP_ENTRAID_URL")
    if entraid_url:
        mcp_tools["entraid"] = complex_client.get_mcp_tool(
            name="entraid_tools",
            url=entraid_url,
            approval_mode="never_require",
        )

    # Email MCP (authenticated via Foundry connection)
    email_url = os.getenv("MCP_EMAIL_URL")
    if email_url:
        mcp_tools["email"] = simple_client.get_mcp_tool(
            name="email_tools",
            url=email_url,
            approval_mode="never_require",
        )

    # ── Create agents ──
    # Instructions come from YAML files, response_format from Pydantic models

    orchestrator = complex_client.as_agent(
        name="Orchestrator",
        instructions=_read_instructions("orchestrator_controlled.yaml"),
        default_options={
            "response_format": OrchestratorResponse,
        },
    )

    support_tools = []
    if "learn" in mcp_tools:
        support_tools.append(mcp_tools["learn"])
    support = simple_client.as_agent(
        name="Support",
        instructions=_read_instructions("support.yaml"),
        tools=support_tools if support_tools else None,
        default_options={"response_format": SupportResponse},
    )

    ticketing_tools = []
    if "cosmosdb" in mcp_tools:
        ticketing_tools.append(mcp_tools["cosmosdb"])
    if "email" in mcp_tools:
        ticketing_tools.append(mcp_tools["email"])
    ticketing_instructions = _read_instructions("ticketing.yaml")
    if user_identity:
        ticketing_instructions += (
            "\n\n## Pre-loaded Authenticated User Identity\n"
            "The following identity was extracted from the authenticated Teams "
            "session. The user IS authenticated — do NOT ask for their name "
            "or email. Use the UserProfile data from the Profiler agent to "
            "fill in the Customer Information section of the ticket.\n\n"
            f"{user_identity}\n\n"
            "Use the User Display Name to greet the user by name."
        )
    ticketing = simple_client.as_agent(
        name="Ticketing",
        instructions=ticketing_instructions,
        tools=ticketing_tools if ticketing_tools else None,
        default_options={"response_format": TicketingResponse},
    )

    profiler_tools = []
    if "entraid" in mcp_tools:
        profiler_tools.append(mcp_tools["entraid"])
    profiler_instructions = _read_instructions("profiler.yaml")
    if user_identity:
        profiler_instructions += (
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
    profiler = complex_client.as_agent(
        name="Profiler",
        instructions=profiler_instructions,
        tools=profiler_tools if profiler_tools else None,
        default_options={"response_format": ProfilerResponse},
    )

    datacollector_tools = []
    if "cosmosdb" in mcp_tools:
        datacollector_tools.append(mcp_tools["cosmosdb"])
    datacollector = standard_client.as_agent(
        name="DataCollector",
        instructions=_read_instructions("dataCollector.yaml"),
        tools=datacollector_tools if datacollector_tools else None,
        default_options={"response_format": DataCollectorResponse},
    )

    communication_tools = []
    if "email" in mcp_tools:
        communication_tools.append(mcp_tools["email"])
    communication = simple_client.as_agent(
        name="Communication",
        instructions=_read_instructions("communication.yaml"),
        tools=communication_tools if communication_tools else None,
        default_options={"response_format": CommunicationResponse},
    )

    # ── Build agent registry ──
    agents = {
        "Orchestrator": orchestrator,
        "Support": support,
        "Ticketing": ticketing,
        "Profiler": profiler,
        "DataCollector": datacollector,
        "Communication": communication,
    }

    # Print loaded agents
    for agent_name in agents:
        print(f"{CYAN}AGENT: {agent_name}{RESET}")

    # ── Create workflow from YAML ──
    factory = WorkflowFactory(agents=agents)
    workflow = factory.create_workflow_from_yaml_path(WORKFLOW_YAML)

    return workflow


async def run_declarative_workflow_streaming(credential: TokenCredential) -> None:
    """
    Run the declarative workflow with streaming output.

    This function creates the workflow, starts it with user input,
    and handles the multi-turn conversation loop via externalLoop
    events from the workflow YAML.

    Args:
        credential: Azure credential for authentication
    """
    print(f"\n{'=' * 60}")
    print("  DistriPartner Platform - Declarative Workflow")
    print(f"{'=' * 60}")
    print("Type your message and press Enter.")
    print(f"Type 'quit' or 'exit' to stop.\n")

    # Create workflow
    workflow = create_declarative_workflow(credential)
    print(f"\n{'=' * 60}\n")

    # Get initial user input
    user_input = input(f"{GREEN}You:{RESET} ").strip()
    if not user_input:
        print("Exiting...")
        return

    pending_request_id: str | None = None
    accumulated_response: str = ""
    last_agent_name: str | None = None

    while True:
        if pending_request_id:
            # Continue workflow with user response
            print(f"\n{YELLOW}WORKFLOW:{RESET} Resume\n")
            response = AgentExternalInputResponse(user_input=user_input)
            stream = workflow.run(
                stream=True, responses={pending_request_id: response}
            )
            pending_request_id = None
        else:
            # Start workflow
            stream = workflow.run(user_input, stream=True)

        async for event in stream:
            if event.type == "output":
                source_id = event.executor_id or ""

                # Check if this is a SendActivity output (log_ prefix)
                if "log_" in source_id.lower():
                    # Print any accumulated agent response first
                    if accumulated_response and last_agent_name:
                        _print_agent_response(last_agent_name, accumulated_response)
                        accumulated_response = ""
                        last_agent_name = None
                    # Print activity message
                    print(f"\n{MAGENTA}ACTIVITY:{RESET} {event.data}")
                else:
                    # Accumulate agent response (streaming text)
                    text = str(event.data) if event.data else ""
                    accumulated_response += text

            elif event.type == "request_info" and isinstance(
                event.data, AgentExternalInputRequest
            ):
                request = event.data
                agent_name = request.agent_name
                agent_response = request.agent_response

                # Print the agent's structured response
                if agent_response:
                    _print_agent_response(agent_name, agent_response)

                # Clear accumulated since we printed from the request
                accumulated_response = ""
                last_agent_name = agent_name

                pending_request_id = event.request_id
                print(f"\n{YELLOW}WORKFLOW:{RESET} Waiting for input")

        # Print any remaining accumulated response at end of stream
        if accumulated_response:
            _print_agent_response(
                last_agent_name or "Agent", accumulated_response
            )
            accumulated_response = ""

        if not pending_request_id:
            break

        # Get next user input
        user_input = input(f"\n{GREEN}You:{RESET} ").strip()
        if not user_input or user_input.lower() in (
            "quit", "exit", "q", "bye", "goodbye", "salir", "adios",
        ):
            print(f"\n{YELLOW}Goodbye!{RESET}")
            break
        print()

    print(f"\n{'=' * 60}")
    print("Workflow Complete")
    print(f"{'=' * 60}")


async def run_declarative_workflow_interactive(credential: TokenCredential) -> None:
    """
    Run the declarative workflow in non-streaming interactive mode.

    Args:
        credential: Azure credential for authentication
    """
    print(f"\n{'=' * 60}")
    print("  DistriPartner Platform - Declarative Workflow (Interactive)")
    print(f"{'=' * 60}")
    print("Type your message and press Enter.")
    print(f"Type 'quit' or 'exit' to stop.\n")

    # Create workflow
    workflow = create_declarative_workflow(credential)
    print(f"\n{'=' * 60}\n")

    # Get initial user input
    user_input = input(f"{GREEN}You:{RESET} ").strip()
    if not user_input:
        print("Exiting...")
        return

    pending_request_id: str | None = None

    while True:
        if pending_request_id:
            response = AgentExternalInputResponse(user_input=user_input)
            result = workflow.run(responses={pending_request_id: response})
            pending_request_id = None
        else:
            result = workflow.run(user_input)

        async for event in result:
            if event.type == "output":
                source_id = event.executor_id or ""
                if "log_" in source_id.lower():
                    print(f"\n{MAGENTA}ACTIVITY:{RESET} {event.data}")
                else:
                    print(f"{CYAN}Agent:{RESET} {event.data}")

            elif event.type == "request_info" and isinstance(
                event.data, AgentExternalInputRequest
            ):
                request = event.data
                if request.agent_response:
                    _print_agent_response(
                        request.agent_name, request.agent_response
                    )
                pending_request_id = event.request_id
                print(f"\n{YELLOW}WORKFLOW:{RESET} Waiting for input")

        if not pending_request_id:
            break

        user_input = input(f"\n{GREEN}You:{RESET} ").strip()
        if not user_input or user_input.lower() in (
            "quit", "exit", "q", "bye", "goodbye", "salir", "adios",
        ):
            print(f"\n{YELLOW}Goodbye!{RESET}")
            break

    print(f"\n{'=' * 60}")
    print("Workflow Complete")
    print(f"{'=' * 60}")


def _print_agent_response(agent_name: str, response_text: str) -> None:
    """Print an agent's response, showing the Response field to the user."""
    try:
        parsed = json.loads(response_text)
        # Show the human-friendly Response field if present
        user_message = parsed.get("Response", "")
        if user_message:
            print(f"\n{CYAN}{agent_name.upper()}:{RESET} {user_message}")
        else:
            # Fallback: show formatted JSON if no Response field
            print(f"\n{CYAN}{agent_name.upper()}:{RESET}")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except (json.JSONDecodeError, TypeError):
        print(f"\n{CYAN}{agent_name.upper()}:{RESET} {response_text}")
