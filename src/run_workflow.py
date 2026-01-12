# =============================================================================
# DistriPartner Platform - Workflow Runner
# =============================================================================
# Script to run the complete hand-off workflow with all agents.
# Uses Microsoft Agent Framework's HandoffBuilder for orchestration.
#
# Usage:
#   python run_workflow.py                    # Run interactive workflow
#   python run_workflow.py --debug            # Run with debug output
#
# Architecture:
#   Orchestrator (coordinator) → Support → Ticketing
#                             → CampaignManager → Profiler/DataCollector/Communication
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
from collections.abc import AsyncIterable
from typing import cast

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agent_framework import (
    ChatMessage,
    HandoffBuilder,
    HandoffUserInputRequest,
    RequestInfoEvent,
    WorkflowEvent,
    WorkflowOutputEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
    Role,
)
from agent_framework_declarative import AgentFactory
from azure.identity.aio import DefaultAzureCredential


# Agent definitions directory
AGENTS_DIR = Path(__file__).parent / "agents" / "definitions"

# Agent YAML files
AGENT_FILES = {
    "orchestrator": "orchestrator.yaml",
    "support": "support.yaml",
    "ticketing": "ticketing.yaml",
    "profiler": "profiler.yaml",
    "dataCollector": "dataCollector.yaml",
    "campaignManager": "campaignmanager.yaml",
    "campaignSuggestor": "campaignSuggestor.yaml",
    "communication": "communication.yaml",
}

# Debug mode flag
DEBUG_MODE = False


def debug_print(*args, **kwargs):
    """Print only if debug mode is enabled."""
    if DEBUG_MODE:
        print("[DEBUG]", *args, **kwargs)


async def drain_stream(stream: AsyncIterable[WorkflowEvent]) -> list[WorkflowEvent]:
    """Collect all events from an async stream into a list."""
    return [event async for event in stream]


def handle_events(events: list[WorkflowEvent]) -> list[RequestInfoEvent]:
    """Process workflow events and extract pending user input requests.
    
    Returns:
        List of RequestInfoEvent for pending user input requests
    """
    requests: list[RequestInfoEvent] = []

    for event in events:
        # Status changes
        if isinstance(event, WorkflowStatusEvent):
            if event.state == WorkflowRunState.IDLE:
                debug_print(f"[Status] Workflow IDLE")
            elif event.state == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS:
                debug_print(f"[Status] Waiting for user input...")

        # Final conversation output
        elif isinstance(event, WorkflowOutputEvent):
            conversation = cast(list[ChatMessage], event.data)
            if isinstance(conversation, list):
                print("\n" + "=" * 60)
                print("📜 CONVERSATION HISTORY")
                print("=" * 60)
                for message in conversation:
                    if not message.text or not message.text.strip():
                        continue
                    speaker = message.author_name or message.role.value
                    icon = "👤" if message.role == Role.USER else "🤖"
                    print(f"\n{icon} {speaker}:")
                    print(f"   {message.text[:500]}{'...' if len(message.text) > 500 else ''}")
                print("\n" + "=" * 60)

        # User input request
        elif isinstance(event, RequestInfoEvent):
            if isinstance(event.data, HandoffUserInputRequest):
                print_agent_responses(event.data)
            requests.append(event)

    return requests


def print_agent_responses(request: HandoffUserInputRequest) -> None:
    """Display agent responses since last user message."""
    if not request.conversation:
        return

    # Find responses since last user message
    agent_responses: list[ChatMessage] = []
    for message in request.conversation[::-1]:
        if message.role == Role.USER:
            break
        if message.text and message.text.strip():
            agent_responses.append(message)

    # Print in original order
    agent_responses.reverse()
    for message in agent_responses:
        speaker = message.author_name or message.role.value
        print(f"\n🤖 {speaker}:")
        print(f"   {message.text}")


async def load_agents(factory: AgentFactory) -> dict:
    """Load all agents from YAML definitions.
    
    Returns:
        Dictionary mapping agent names to agent instances
    """
    agents = {}
    
    print("\n📦 Loading agents...")
    print("-" * 50)
    
    for name, filename in AGENT_FILES.items():
        yaml_path = AGENTS_DIR / filename
        if yaml_path.exists():
            try:
                agent = factory.create_agent_from_yaml_path(yaml_path)
                agents[name] = agent
                print(f"   ✅ {name:<20} loaded")
            except Exception as e:
                print(f"   ⚠️  {name:<20} failed: {e}")
        else:
            print(f"   ❌ {name:<20} not found: {yaml_path}")
    
    print("-" * 50)
    print(f"   Total: {len(agents)}/{len(AGENT_FILES)} agents loaded\n")
    
    return agents


def build_workflow(agents: dict):
    """Build the hand-off workflow with all agents.
    
    Workflow structure:
    - Orchestrator is the coordinator (entry point)
    - Orchestrator can hand off to: Support, CampaignManager
    - Support can hand off to: Ticketing
    - Ticketing can hand off to: Profiler, DataCollector
    - CampaignManager can hand off to: Profiler, DataCollector, Communication, CampaignSuggestor
    """
    
    # Get agent instances
    orchestrator = agents.get("orchestrator")
    support = agents.get("support")
    ticketing = agents.get("ticketing")
    profiler = agents.get("profiler")
    data_collector = agents.get("dataCollector")
    campaign_manager = agents.get("campaignManager")
    campaign_suggestor = agents.get("campaignSuggestor")
    communication = agents.get("communication")
    
    if not orchestrator:
        raise ValueError("Orchestrator agent is required but not loaded")
    
    # Get all available participants (exclude None values)
    participants = [a for a in [
        orchestrator, support, ticketing, profiler, 
        data_collector, campaign_manager, campaign_suggestor, communication
    ] if a is not None]
    
    print(f"🔧 Building workflow with {len(participants)} participants...")
    
    # Build the handoff workflow
    builder = HandoffBuilder(
        name="distripartner_workflow",
        participants=participants,
    ).set_coordinator(orchestrator)
    
    # Configure hand-off routes
    # Orchestrator can route to main agents
    if support:
        builder.add_handoff(orchestrator, [support])
        debug_print("   Route: orchestrator → support")
    if campaign_manager:
        builder.add_handoff(orchestrator, [campaign_manager])
        debug_print("   Route: orchestrator → campaignManager")
    
    # Support can escalate to ticketing
    if support and ticketing:
        builder.add_handoff(support, [ticketing])
        debug_print("   Route: support → ticketing")
    
    # Ticketing can get data from profiler and dataCollector
    if ticketing:
        data_agents = [a for a in [profiler, data_collector] if a]
        if data_agents:
            builder.add_handoff(ticketing, data_agents)
            debug_print(f"   Route: ticketing → {[type(a).__name__ for a in data_agents]}")
    
    # CampaignManager can use data agents and communication
    if campaign_manager:
        campaign_targets = [a for a in [profiler, data_collector, communication, campaign_suggestor] if a]
        if campaign_targets:
            builder.add_handoff(campaign_manager, campaign_targets)
            debug_print(f"   Route: campaignManager → {len(campaign_targets)} agents")
    
    # Add termination condition: stop when user says goodbye/thanks/exit
    workflow = builder.with_termination_condition(
        lambda conv: (
            len(conv) > 0 and 
            conv[-1].role == Role.USER and 
            any(word in conv[-1].text.lower() for word in ["adios", "adiós", "bye", "exit", "salir", "gracias", "thanks"])
        )
    ).build()
    
    print("✅ Workflow built successfully!\n")
    return workflow


async def run_workflow(debug: bool = False):
    """Run the complete hand-off workflow interactively."""
    global DEBUG_MODE
    DEBUG_MODE = debug
    
    # Check required environment variables
    required_vars = ["AZURE_AI_PROJECT_ENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Copy .env.fake to .env and fill in your values.")
        return
    
    # Create credential for Azure authentication
    credential = DefaultAzureCredential()
    
    try:
        # Create agent factory
        factory = AgentFactory(
            client_kwargs={
                "credential": credential,
                "project_endpoint": os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            },
            env_file_path=str(Path(__file__).parent.parent / ".env"),
            safe_mode=False
        )
        
        # Load all agents
        agents = await load_agents(factory)
        
        if len(agents) < 2:
            print("❌ Not enough agents loaded. Need at least 2 agents for workflow.")
            return
        
        # Build the workflow
        workflow = build_workflow(agents)
        
        print("=" * 60)
        print("  💬 DistriPartner Interactive Workflow")
        print("=" * 60)
        print("\n📌 Instructions:")
        print("   - Type your message and press Enter")
        print("   - The orchestrator will route you to the right agent")
        print("   - Say 'adiós', 'gracias' or 'exit' to end the conversation")
        print("-" * 60)
        
        # Get initial message
        print("\n👤 You: ", end="", flush=True)
        initial_message = input().strip()
        
        if not initial_message:
            initial_message = "Hola, necesito ayuda"
        
        # Start the workflow
        print("\n⏳ Processing...")
        events = await drain_stream(workflow.run_stream(initial_message))
        pending_requests = handle_events(events)
        
        # Interactive loop
        while pending_requests:
            try:
                print("\n👤 You: ", end="", flush=True)
                user_input = input().strip()
                
                if not user_input:
                    continue
                
                # Check for exit
                if user_input.lower() in ["quit", "q"]:
                    print("\n👋 Workflow interrupted. Goodbye!")
                    break
                
                # Send response to all pending requests
                responses = {req.request_id: user_input for req in pending_requests}
                
                print("\n⏳ Processing...")
                events = await drain_stream(workflow.send_responses_streaming(responses))
                pending_requests = handle_events(events)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
        
        if not pending_requests:
            print("\n✅ Workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        print("\n💡 Make sure you have:")
        print("   1. Copied .env.fake to .env with valid credentials")
        print("   2. Logged in with: az login")
        print("   3. Installed requirements: pip install -r requirements.txt")
        
    finally:
        await credential.close()


def main():
    parser = argparse.ArgumentParser(
        description="Run the DistriPartner hand-off workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python run_workflow.py           # Run interactive workflow
  python run_workflow.py --debug   # Run with debug output

The workflow routes requests through multiple agents:
  Orchestrator → Support → Ticketing → Profiler/DataCollector
              → CampaignManager → Communication/CampaignSuggestor
        """
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug output"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  🚀 DistriPartner Platform - Workflow Runner")
    print("=" * 60)
    
    asyncio.run(run_workflow(debug=args.debug))


if __name__ == "__main__":
    main()
