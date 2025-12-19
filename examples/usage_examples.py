"""
Example usage of the Microsoft Agent Framework workflow.

This script demonstrates the agent structure and workflow patterns.
"""

import os
import asyncio
from dotenv import load_dotenv


async def example_support_query():
    """Example: Technical support query."""
    print("\n" + "=" * 60)
    print("Example 1: Technical Support Query")
    print("=" * 60)
    
    print("\nAgent Structure:")
    print("  - Support Agent with MCP server + Azure AI Search tools")
    print("  - Orchestrator routes technical questions to Support Agent")
    
    print("\nExample flow for: 'How do I configure Azure AD?'")
    print("  1. Orchestrator receives question")
    print("  2. Routes to Support Agent")
    print("  3. Support Agent searches knowledge base using Azure AI Search")
    print("  4. Uses MCP server for additional context")
    print("  5. Provides step-by-step guidance")
    print("  6. Returns control to Orchestrator")


async def example_ticket_creation():
    """Example: Ticket creation."""
    print("\n" + "=" * 60)
    print("Example 2: Ticket Creation")
    print("=" * 60)
    
    print("\nAgent Structure:")
    print("  - Ticket Agent with Partner Center API integration")
    print("  - Orchestrator routes ticket requests to Ticket Agent")
    
    print("\nExample flow for: 'I need to report a critical issue'")
    print("  1. Orchestrator receives request")
    print("  2. Routes to Ticket Agent")
    print("  3. Ticket Agent collects issue details (title, description, priority)")
    print("  4. Authenticates with Partner Center API")
    print("  5. Creates the support ticket")
    print("  6. Provides ticket ID and confirmation")
    print("  7. Returns control to Orchestrator")


async def example_database_query():
    """Example: Database query."""
    print("\n" + "=" * 60)
    print("Example 3: Database Query")
    print("=" * 60)
    
    print("\nAgent Structure:")
    print("  - Database Agent with Azure Cosmos DB integration")
    print("  - Orchestrator routes data queries to Database Agent")
    
    print("\nExample flow for: 'Find customer 12345'")
    print("  1. Orchestrator receives query")
    print("  2. Routes to Database Agent")
    print("  3. Database Agent queries Azure Cosmos DB")
    print("  4. Retrieves customer information")
    print("  5. Formats and presents the results")
    print("  6. Returns control to Orchestrator")


async def example_campaign_creation():
    """Example: Campaign creation."""
    print("\n" + "=" * 60)
    print("Example 4: Campaign Creation")
    print("=" * 60)
    
    print("\nAgent Structure:")
    print("  - Campaign Agent for marketing and distributor actions")
    print("  - Orchestrator routes campaign requests to Campaign Agent")
    
    print("\nExample flow for: 'Create Q1 email campaign'")
    print("  1. Orchestrator receives request")
    print("  2. Routes to Campaign Agent")
    print("  3. Campaign Agent collects details (name, type, dates, budget)")
    print("  4. Validates parameters")
    print("  5. Creates and schedules the campaign")
    print("  6. Provides campaign ID and status")
    print("  7. Returns control to Orchestrator")


async def example_full_workflow():
    """Example: Full workflow with all agents."""
    print("\n" + "=" * 60)
    print("Example 5: Full Multi-Agent Workflow")
    print("=" * 60)
    
    print("\nComplete Agent Architecture:")
    print("  ┌─────────────────────────────────────┐")
    print("  │      Orchestrator Agent             │")
    print("  │   (Routes user interactions)        │")
    print("  └────────┬───────┬────────┬───────────┘")
    print("           │       │        │        ")
    print("     ┌─────┴──┐ ┌──┴────┐ ┌┴─────────┐")
    print("     │Support │ │Ticket │ │Database  │ ...")
    print("     │Agent   │ │Agent  │ │Agent     │")
    print("     └────────┘ └───────┘ └──────────┘")
    
    print("\nOrchestrator can route to:")
    print("  • Support Agent - Technical questions and documentation")
    print("  • Ticket Agent - Support ticket management")
    print("  • Database Agent - Data queries and retrieval")
    print("  • Campaign Agent - Campaign execution and management")
    print("\nAll agents use handoff pattern for seamless interaction")
    print("Users work with Orchestrator which delegates to specialists")


async def main():
    """Run all examples."""
    # Load environment (if .env exists)
    load_dotenv()
    
    print("\n" + "=" * 60)
    print("Microsoft Agent Framework - Usage Examples")
    print("=" * 60)
    
    # Check if Azure OpenAI is configured
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("\n⚠ Azure OpenAI is not configured!")
        print("\nThese examples demonstrate agent structure without live execution.")
        print("To run the agents with actual Azure AI, configure .env first.\n")
    
    # Run examples
    await example_support_query()
    await example_ticket_creation()
    await example_database_query()
    await example_campaign_creation()
    await example_full_workflow()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nTo run the actual agent workflow:")
    print("  python src/main.py")
    print("\nMake sure to configure .env with your credentials first:")
    print("  cp .env.example .env")
    print("  # Edit .env with your settings")
    print()


if __name__ == "__main__":
    asyncio.run(main())
