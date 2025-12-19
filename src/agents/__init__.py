"""
Agent module for Microsoft Agent Framework workflow.

This module contains all the specialized agents for the support system:
- Orchestrator Agent: Routes user interactions
- Support Agent: Technical support and documentation
- Ticket Agent: Support ticket management
- Database Agent: Data queries and retrieval
- Campaign Agent: Campaign execution and management
- Notification Agent: Email notifications (skeleton)
"""

from .orchestrator_agent import OrchestratorAgent, create_orchestrator_agent
from .support_agent import SupportAgent, create_support_agent
from .ticket_agent import TicketAgent, create_ticket_agent
from .database_agent import DatabaseAgent, create_database_agent
from .campaign_agent import CampaignAgent, create_campaign_agent
from .notification_agent import NotificationAgent, create_notification_agent

__all__ = [
    # Classes
    "OrchestratorAgent",
    "SupportAgent",
    "TicketAgent",
    "DatabaseAgent",
    "CampaignAgent",
    "NotificationAgent",
    # Factory functions
    "create_orchestrator_agent",
    "create_support_agent",
    "create_ticket_agent",
    "create_database_agent",
    "create_campaign_agent",
    "create_notification_agent",
]
