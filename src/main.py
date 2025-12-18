"""
Main application for Microsoft Agent Framework workflow.

This module sets up and runs the agent workflow with orchestration pattern.
"""

import os
import asyncio
from dotenv import load_dotenv
from agent_framework import Runner

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
        Tuple of (orchestrator_agent, all_agents_list)
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

    # Return orchestrator and list of all agents
    all_agents = [
        orchestrator_agent,
        support_agent,
        ticket_agent,
        database_agent,
        campaign_agent,
        notification_agent,
    ]

    return orchestrator_agent, all_agents


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
    print("Setting up agents...")
    
    # Set up agents
    orchestrator_agent, all_agents = setup_agents()
    
    print("✓ Orchestrator Agent initialized")
    print("✓ Support Agent initialized")
    print("✓ Ticket Agent initialized")
    print("✓ Database Agent initialized")
    print("✓ Campaign Agent initialized")
    print("✓ Notification Agent initialized (skeleton)")
    print()
    print("Starting agent workflow...")
    print("=" * 60)
    print()

    # Create runner with orchestrator as the entry point
    runner = Runner(
        agent=orchestrator_agent,
        agents=all_agents,
    )

    # Example: Run with a sample message
    # In a real application, this would be connected to a UI or API
    sample_message = "Hello, I need help with a technical issue."
    
    print(f"User: {sample_message}")
    print()
    
    try:
        # Run the agent
        result = await runner.run(
            messages=[{"role": "user", "content": sample_message}]
        )
        
        print("Agent Response:")
        for message in result.messages:
            if message.get("role") == "assistant":
                print(f"Assistant: {message.get('content', '')}")
        
        print()
        print("=" * 60)
        print("Workflow completed successfully!")
        
    except Exception as e:
        print(f"Error running workflow: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the application."""
    # Run the async workflow
    asyncio.run(run_agent_workflow())


if __name__ == "__main__":
    main()
