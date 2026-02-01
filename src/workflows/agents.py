# =============================================================================
# DistriPartner Platform - Agent Loading
# =============================================================================
# Functions to load declarative agents from YAML definitions.
# Agents are defined in YAML but workflows are programmatic (Python).
# =============================================================================

import os
from pathlib import Path
from typing import Any

from agent_framework_declarative import AgentFactory
from agent_framework import ChatAgent
from azure.identity.aio import DefaultAzureCredential


def get_agents_dir() -> Path:
    """Get the path to the agents definitions directory."""
    return Path(__file__).parent.parent / "agents" / "definitions"


def get_env_file_path() -> Path:
    """Get the path to the .env file."""
    return Path(__file__).parent.parent.parent / ".env"


def _create_agent_factory(credential: DefaultAzureCredential) -> AgentFactory:
    """
    Create an AgentFactory with Azure credentials.
    
    Args:
        credential: Azure credential for authentication
        
    Returns:
        Configured AgentFactory instance
    """
    return AgentFactory(
        client_kwargs={
            "credential": credential,
            "project_endpoint": os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
        },
        env_file_path=str(get_env_file_path()),
        safe_mode=False,  # Allow PowerFx expressions for environment variables
    )


async def load_agent_from_yaml(
    yaml_filename: str,
    credential: DefaultAzureCredential,
) -> ChatAgent:
    """
    Load a single agent from a YAML definition file.
    
    Args:
        yaml_filename: Name of the YAML file (e.g., "support.yaml")
        credential: Azure credential for authentication
        
    Returns:
        Loaded ChatAgent instance
    """
    factory = _create_agent_factory(credential)
    yaml_path = get_agents_dir() / yaml_filename
    
    if not yaml_path.exists():
        raise FileNotFoundError(f"Agent definition not found: {yaml_path}")
    
    return factory.create_agent_from_yaml_path(yaml_path)


async def load_orchestrator_native(credential: DefaultAzureCredential) -> ChatAgent:
    """
    Load the Orchestrator agent configured for Native handoff mode.
    
    In Native mode, the Orchestrator uses auto-generated handoff tool calls
    (handoff_to_support, handoff_to_ticketing) to route conversations.
    
    Args:
        credential: Azure credential for authentication
        
    Returns:
        Orchestrator agent configured for Native mode
    """
    return await load_agent_from_yaml("orchestrator_native.yaml", credential)


async def load_orchestrator_controlled(credential: DefaultAzureCredential) -> ChatAgent:
    """
    Load the Orchestrator agent configured for Controlled handoff mode.
    
    In Controlled mode, the Orchestrator returns JSON with an Intent field,
    and Python code interprets the intent to force handoffs.
    
    Args:
        credential: Azure credential for authentication
        
    Returns:
        Orchestrator agent configured for Controlled mode
    """
    return await load_agent_from_yaml("orchestrator_controlled.yaml", credential)


async def load_support_agent(credential: DefaultAzureCredential) -> ChatAgent:
    """
    Load the Support agent.
    
    The Support agent handles first-level support using:
    - file_search: RAG retrieval from Azure AI Search knowledge base
    - mcp: Microsoft Learn documentation search
    
    Args:
        credential: Azure credential for authentication
        
    Returns:
        Support agent instance
    """
    return await load_agent_from_yaml("support.yaml", credential)


async def load_ticketing_agent(credential: DefaultAzureCredential) -> ChatAgent:
    """
    Load the Ticketing agent.
    
    The Ticketing agent handles support ticket creation:
    - Gathers issue information through conversation
    - Stores tickets in CosmosDB
    - Sends email notifications
    
    Args:
        credential: Azure credential for authentication
        
    Returns:
        Ticketing agent instance
    """
    return await load_agent_from_yaml("ticketing.yaml", credential)


async def load_all_agents(
    credential: DefaultAzureCredential,
    mode: str = "native",
) -> dict[str, ChatAgent]:
    """
    Load all agents needed for the workflow.
    
    Args:
        credential: Azure credential for authentication
        mode: Either "native" or "controlled" for Orchestrator variant
        
    Returns:
        Dictionary mapping agent names to ChatAgent instances
    """
    if mode == "native":
        orchestrator = await load_orchestrator_native(credential)
    elif mode == "controlled":
        orchestrator = await load_orchestrator_controlled(credential)
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'native' or 'controlled'.")
    
    support = await load_support_agent(credential)
    ticketing = await load_ticketing_agent(credential)
    
    return {
        "orchestrator": orchestrator,
        "support": support,
        "ticketing": ticketing,
    }
