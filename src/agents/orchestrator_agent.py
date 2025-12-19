"""
Orchestrator Agent for the Microsoft Agent Framework workflow.

This agent routes user interactions to the appropriate specialized agent:
- Support Agent: Technical questions and documentation
- Ticket Agent: Creating support tickets
- Database Agent: Data queries
- Campaign Agent: Distributor actions
"""

from agent_framework import ChatAgent
from typing import Optional
from .utils import create_azure_ai_client


class OrchestratorAgent:
    """
    Orchestrator Agent that manages user interactions and routes them to specialized agents.
    Uses returnToPrevious handoff pattern for better user experience.
    """

    def __init__(
        self,
        support_agent: Optional["ChatAgent"] = None,
        ticket_agent: Optional["ChatAgent"] = None,
        database_agent: Optional["ChatAgent"] = None,
        campaign_agent: Optional["ChatAgent"] = None,
    ):
        """
        Initialize the Orchestrator Agent.

        Args:
            support_agent: Agent for technical support and documentation
            ticket_agent: Agent for ticket creation
            database_agent: Agent for database queries
            campaign_agent: Agent for campaign actions
        """
        self.support_agent = support_agent
        self.ticket_agent = ticket_agent
        self.database_agent = database_agent
        self.campaign_agent = campaign_agent

        # Create the orchestrator agent
        chat_client = create_azure_ai_client()
        self.agent = chat_client.create_agent(
            name="orchestrator",
            instructions=self._get_instructions(),
            tools=self._get_handoff_tools(),
        )

    def _get_instructions(self) -> str:
        """Get the system instructions for the orchestrator agent."""
        return """You are the Orchestrator Agent for a Microsoft Partner support system.

Your role is to understand the user's needs and direct them to the appropriate specialist:

1. **Support Agent**: For technical questions, documentation, product information, and general inquiries.
   - Use when users ask "how to" questions
   - Use for troubleshooting and technical guidance
   - Use for product documentation requests

2. **Ticket Agent**: For creating support tickets in the Microsoft Partner Center.
   - Use when users want to report issues
   - Use when users need to escalate problems
   - Use when users explicitly request ticket creation

3. **Database Agent**: For querying information from the system database.
   - Use when users need data retrieval
   - Use for historical information lookup
   - Use for reporting and analytics queries

4. **Campaign Agent**: For executing actions on behalf of distributors.
   - Use for marketing campaign management
   - Use for distributor-specific actions
   - Use for campaign execution requests

Always:
- Greet users warmly and understand their needs
- Route to the appropriate agent based on the request
- Provide clear explanations when transferring to another agent
- Handle ambiguous requests by asking clarifying questions
- Return users to you after the specialist completes their task

Be concise, professional, and helpful."""

    def _get_handoff_tools(self) -> list:
        """
        Get handoff tools for routing to specialized agents.
        """
        tools = []

        # Add handoffs to available agents using HandoffBuilder
        if self.support_agent:
            support_handoff = HandoffBuilder(
                target_agent=self.support_agent,
                name="Support Agent",
                description=(
                    "Route technical questions, documentation requests, and general "
                    "product inquiries to the Support Agent."
                ),
            ).build()
            tools.append(support_handoff)

        if self.ticket_agent:
            ticket_handoff = HandoffBuilder(
                target_agent=self.ticket_agent,
                name="Ticket Agent",
                description=(
                    "Route issue reports and escalation or ticket creation requests "
                    "to the Ticket Agent."
                ),
            ).build()
            tools.append(ticket_handoff)

        if self.database_agent:
            database_handoff = HandoffBuilder(
                target_agent=self.database_agent,
                name="Database Agent",
                description=(
                    "Route data retrieval, historical lookup, reporting, and "
                    "analytics queries to the Database Agent."
                ),
            ).build()
            tools.append(database_handoff)

        if self.campaign_agent:
            campaign_handoff = HandoffBuilder(
                target_agent=self.campaign_agent,
                name="Campaign Agent",
                description=(
                    "Route distributor actions and marketing campaign management "
                    "requests to the Campaign Agent."
                ),
            ).build()
            tools.append(campaign_handoff)
        return tools

    def get_agent(self):
        """Return the configured agent instance."""
        return self.agent


def create_orchestrator_agent(
    support_agent=None,
    ticket_agent=None,
    database_agent=None,
    campaign_agent=None,
):
    """
    Factory function to create and return an Orchestrator Agent.

    Args:
        support_agent: Support Agent instance
        ticket_agent: Ticket Agent instance
        database_agent: Database Agent instance
        campaign_agent: Campaign Agent instance

    Returns:
        Configured agent for orchestration
    """
    orchestrator = OrchestratorAgent(
        support_agent=support_agent,
        ticket_agent=ticket_agent,
        database_agent=database_agent,
        campaign_agent=campaign_agent,
    )
    return orchestrator.get_agent()
