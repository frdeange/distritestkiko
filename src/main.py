"""
Main application for Microsoft Agent Framework workflow.

This module sets up and runs the agent workflow with orchestration pattern.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from agents import (
    create_orchestrator_agent,
    create_support_agent,
    create_ticket_agent,
    create_database_agent,
    create_campaign_agent,
    create_notification_agent,
)


def setup_agents():
    """
    Set up all agents with their configurations.
    
    Returns:
        orchestrator_agent
    """
    # Create specialized agents
    support_agent = create_support_agent()
    ticket_agent = create_ticket_agent()
    database_agent = create_database_agent()
    campaign_agent = create_campaign_agent()
    notification_agent = create_notification_agent()

    # Create orchestrator with handoffs to all specialized agents
    orchestrator_agent = create_orchestrator_agent(
        support_agent=support_agent,
        ticket_agent=ticket_agent,
        database_agent=database_agent,
        campaign_agent=campaign_agent,
    )

    return orchestrator_agent


async def run_agent_workflow():
    """
    Run the agent workflow with the orchestrator as the entry point.
    """
    # Load environment variables
    load_dotenv()

    print("=" * 60)
    print("Microsoft Agent Framework - Support System")
    print("=" * 60)
    print()
    
    # Check if Azure OpenAI is configured
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("⚠ Azure OpenAI is not configured!")
        print()
        print("This is a Proof of Concept implementation that requires Azure credentials.")
        print()
        print("To run the agents, you need to:")
        print("1. Copy .env.example to .env")
        print("2. Configure your Azure OpenAI credentials in .env:")
        print("   - AZURE_OPENAI_ENDPOINT")
        print("   - AZURE_OPENAI_API_KEY") 
        print("   - AZURE_OPENAI_DEPLOYMENT_NAME")
        print()
        print("For now, here's what the implementation includes:")
        print()
        print("✓ Orchestrator Agent - Routes user interactions")
        print("✓ Support Agent - Technical support with MCP + Azure AI Search")
        print("✓ Ticket Agent - Creates tickets in Partner Center")
        print("✓ Database Agent - Queries Azure Cosmos DB")
        print("✓ Campaign Agent - Manages campaigns")
        print("✓ Notification Agent - Email notifications (skeleton)")
        print()
        print("See README.md for complete setup instructions.")
        print("See examples/usage_examples.py for code examples.")
        print("=" * 60)
        return
    
    print("Setting up agents...")
    
    try:
        # Set up agents
        orchestrator_agent = setup_agents()
        
        print("✓ Orchestrator Agent initialized")
        print("✓ Support Agent initialized")
        print("✓ Ticket Agent initialized")
        print("✓ Database Agent initialized")
        print("✓ Campaign Agent initialized")
        print("✓ Notification Agent initialized (skeleton)")
        print()
        print("Agent workflow is ready!")
        print("=" * 60)
        print()
        print("NOTE: This is a PoC implementation.")
        print("To interact with the agents, you need to:")
        print("1. Integrate with a UI or API endpoint")
        print("2. Use the agent.run() or similar method from the framework")
        print()
        print("See examples/usage_examples.py for demonstrations of agent capabilities.")
        print()
    except Exception as e:
        print(f"✗ Error setting up agents: {e}")
        print()
        print("Please check your configuration in .env and try again.")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the application."""
    # Run the async workflow
    asyncio.run(run_agent_workflow())


if __name__ == "__main__":
    main()
