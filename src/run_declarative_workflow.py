# =============================================================================
# DistriPartner Platform - Declarative Workflow Runner
# =============================================================================
# Script to run the declarative YAML workflow using WorkflowFactory.
# Loads agents from YAML definitions and executes the multi-agent workflow.
#
# Usage:
#   python run_declarative_workflow.py                 # Run interactive workflow
#   python run_declarative_workflow.py --debug         # Run with debug output
#   python run_declarative_workflow.py --input "msg"   # Run with initial input
#
# Architecture:
#   Orchestrator (entry) → Support (L1) ↔ Ticketing (escalation)
#
# Requirements:
#   - Copy .env.fake to .env and fill in your Azure AI credentials
#   - Run: az login (for Azure CLI authentication)
#   - Install: pip install -r requirements.txt
# =============================================================================

import asyncio
import argparse
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agent_framework import (
    WorkflowOutputEvent,
    WorkflowStatusEvent,
    WorkflowRunState,
)
from agent_framework.declarative import AgentFactory, WorkflowFactory
from azure.identity.aio import DefaultAzureCredential

# Paths
WORKFLOW_DIR = Path(__file__).parent / "agents" / "workflow"
AGENTS_DIR = Path(__file__).parent / "agents" / "definitions"
WORKFLOW_FILE = WORKFLOW_DIR / "main-workflow.yaml"

# Agent YAML files used in the workflow
WORKFLOW_AGENTS = {
    "Orchestrator": "orchestrator.yaml",
    "Support": "support.yaml",
    "Ticketing": "ticketing.yaml",
}

# Debug mode flag
DEBUG_MODE = False

# Global credential for Azure authentication
CREDENTIAL: DefaultAzureCredential | None = None


def debug_print(*args: Any, **kwargs: Any) -> None:
    """Print only if debug mode is enabled."""
    if DEBUG_MODE:
        print("[DEBUG]", *args, **kwargs)


def print_banner() -> None:
    """Print the application banner."""
    print()
    print("=" * 60)
    print("  🤖 DistriPartner Platform - Declarative Workflow")
    print("=" * 60)
    print()
    print("  Workflow: Orchestrator → Support ↔ Ticketing")
    print("  Mode: Declarative YAML with InvokeAzureAgent")
    print()
    print("-" * 60)
    print()


async def create_agents(agent_factory: AgentFactory) -> dict[str, Any]:
    """Load all workflow agents from YAML definitions.
    
    Args:
        agent_factory: AgentFactory instance for creating agents from YAML
        
    Returns:
        Dictionary mapping agent names to agent instances
    """
    agents = {}
    
    for agent_name, yaml_file in WORKFLOW_AGENTS.items():
        yaml_path = AGENTS_DIR / yaml_file
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"Agent definition not found: {yaml_path}")
        
        debug_print(f"Loading agent '{agent_name}' from {yaml_file}")
        
        # Use async method for provider-based agent creation (AzureAIAgentClient)
        agent = await agent_factory.create_agent_from_yaml_path_async(yaml_path)
        agents[agent_name] = agent
        
        print(f"  ✅ Loaded agent: {agent_name}")
    
    return agents


async def run_workflow(initial_input: str | None = None) -> None:
    """Run the declarative workflow.
    
    Args:
        initial_input: Optional initial message to start the workflow
    """
    global CREDENTIAL
    
    print_banner()
    
    # Validate environment
    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    if not endpoint:
        print("❌ Error: AZURE_AI_PROJECT_ENDPOINT not set in environment")
        print("   Please copy .env.fake to .env and configure your credentials")
        return
    
    print(f"📡 Connecting to: {endpoint[:50]}...")
    print()
    
    # Create Azure credential
    CREDENTIAL = DefaultAzureCredential()
    
    # Create agent factory with credential and safe_mode=False to enable PowerFx =Env. resolution
    print("📦 Loading agents...")
    agent_factory = AgentFactory(
        client_kwargs={"credential": CREDENTIAL},
        safe_mode=False,  # Allow PowerFx env var resolution (=Env.VAR_NAME)
    )
    agents = await create_agents(agent_factory)
    print()
    
    # Create workflow factory with agents
    print("🔧 Initializing workflow...")
    workflow_factory = WorkflowFactory(agents=agents)
    
    # Load workflow from YAML
    if not WORKFLOW_FILE.exists():
        print(f"❌ Error: Workflow file not found: {WORKFLOW_FILE}")
        return
    
    workflow = workflow_factory.create_workflow_from_yaml_path(WORKFLOW_FILE)
    print(f"  ✅ Loaded workflow: {workflow.name}")
    print()
    
    print("=" * 60)
    print("  💬 Starting conversation (type 'exit' to quit)")
    print("=" * 60)
    print()
    
    # Get initial input
    if initial_input:
        user_input = initial_input
        print(f"You: {user_input}")
    else:
        user_input = input("You: ").strip()
    
    if not user_input or user_input.lower() == "exit":
        print("👋 Goodbye!")
        return
    
    # Run workflow with streaming
    pending_request = None
    
    while True:
        try:
            # Execute workflow
            async for event in workflow.run_stream(user_input):
                # Handle status events
                if isinstance(event, WorkflowStatusEvent):
                    if event.state == WorkflowRunState.IDLE:
                        debug_print("Workflow IDLE")
                    elif event.state == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS:
                        debug_print("Waiting for user input...")
                        pending_request = event
                
                # Handle output events (conversation complete)
                elif isinstance(event, WorkflowOutputEvent):
                    if hasattr(event, 'data') and event.data:
                        print(f"\n📄 Output: {event.data}")
                    debug_print(f"Workflow output: {event.data}")
                
                # Handle agent responses - try to extract and display text
                else:
                    # Try various ways to get the response text from the event
                    response_text = None
                    
                    # Check for 'text' attribute
                    if hasattr(event, 'text') and event.text:
                        response_text = event.text
                    # Check for 'data' attribute
                    elif hasattr(event, 'data') and event.data:
                        if isinstance(event.data, str):
                            response_text = event.data
                        elif isinstance(event.data, dict) and 'text' in event.data:
                            response_text = event.data['text']
                    # Check for message content
                    elif hasattr(event, 'message') and event.message:
                        if hasattr(event.message, 'text'):
                            response_text = event.message.text
                    
                    if response_text:
                        print(f"\n🤖 Agent: {response_text}")
                    else:
                        debug_print(f"Event type: {type(event).__name__}, attrs: {dir(event)[:5]}")
            
            # Check if workflow needs more input
            if pending_request:
                print()
                user_input = input("You: ").strip()
                
                if not user_input or user_input.lower() == "exit":
                    print("👋 Goodbye!")
                    break
                
                pending_request = None
            else:
                # Workflow completed
                print()
                print("=" * 60)
                print("  ✅ Workflow completed")
                print("=" * 60)
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            break


def main() -> None:
    """Main entry point."""
    global DEBUG_MODE
    
    parser = argparse.ArgumentParser(
        description="Run DistriPartner declarative workflow"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Initial input message"
    )
    
    args = parser.parse_args()
    DEBUG_MODE = args.debug
    
    if DEBUG_MODE:
        print("[DEBUG MODE ENABLED]")
    
    asyncio.run(run_workflow(args.input))


if __name__ == "__main__":
    main()
