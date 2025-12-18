"""
Ticket Agent for the Microsoft Agent Framework workflow.

This agent handles creating support tickets in the Microsoft Partner Center
using OpenAPI integration.
"""

from agent_framework import ai_function
from typing import Any, Dict, Optional
import os
import httpx
from datetime import datetime, timezone
from .utils import create_azure_ai_client


class TicketAgent:
    """
    Ticket Agent that creates support tickets in Microsoft Partner Center.
    """

    def __init__(
        self,
        partner_center_endpoint: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize the Ticket Agent.

        Args:
            partner_center_endpoint: Microsoft Partner Center API endpoint
            tenant_id: Azure AD tenant ID
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
        """
        self.partner_center_endpoint = partner_center_endpoint or os.getenv("PARTNER_CENTER_API_ENDPOINT")
        self.tenant_id = tenant_id or os.getenv("PARTNER_CENTER_TENANT_ID")
        self.client_id = client_id or os.getenv("PARTNER_CENTER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("PARTNER_CENTER_CLIENT_SECRET")
        
        self._access_token = None

        # Create the ticket agent
        chat_client = create_azure_ai_client()
        self.agent = chat_client.create_agent(
            name="ticket",
            instructions=self._get_instructions(),
            tools=self._setup_tools(),
        )

    def _get_instructions(self) -> str:
        """Get the system instructions for the ticket agent."""
        return """You are the Ticket Agent for a Microsoft Partner support system.

Your role is to help users create support tickets in the Microsoft Partner Center.

Capabilities:
- Collect necessary information for ticket creation
- Create tickets with appropriate priority and category
- Provide ticket confirmation and reference numbers
- Guide users through the ticket creation process

Guidelines:
- Always collect: title, description, priority, and category
- Validate information before creating the ticket
- Ask clarifying questions if details are incomplete
- Provide clear confirmation when ticket is created
- Include ticket ID and next steps in your response
- Be empathetic when handling user issues

Priority levels:
- Critical: System down, major impact on business
- High: Important functionality impaired
- Medium: Partial functionality issues
- Low: Minor issues, questions, or requests

When you've completed creating the ticket, let them know they'll be returned to the orchestrator."""

    def _setup_tools(self) -> list:
        """Set up tools for the ticket agent."""
        return [
            self._create_ticket_tool(),
            self._check_ticket_status_tool(),
        ]

    def _create_ticket_tool(self):
        """Create an AI function for creating support tickets."""

        @ai_function
        async def create_support_ticket(
            title: str,
            description: str,
            priority: str = "Medium",
            category: str = "General",
        ) -> Dict[str, Any]:
            """
            Create a support ticket in Microsoft Partner Center.

            Args:
                title: Brief title of the issue
                description: Detailed description of the problem
                priority: Priority level (Critical, High, Medium, Low)
                category: Issue category (General, Technical, Billing, etc.)

            Returns:
                Ticket creation result with ticket ID
            """
            if not all([self.partner_center_endpoint, self.tenant_id, self.client_id, self.client_secret]):
                return {
                    "success": False,
                    "error": "Partner Center API is not configured",
                    "ticket_id": None
                }

            try:
                # Get access token if needed
                if not self._access_token:
                    await self._get_access_token()

                # Prepare ticket data
                ticket_data = {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "category": category,
                    "status": "Open",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

                # Create ticket via API
                headers = {
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.partner_center_endpoint}/v1/tickets",
                        headers=headers,
                        json=ticket_data,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    return {
                        "success": True,
                        "ticket_id": result.get("ticket_id", "UNKNOWN"),
                        "status": result.get("status", "Open"),
                        "created_at": result.get("created_at"),
                        "message": "Ticket created successfully"
                    }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to create ticket: {str(e)}",
                    "ticket_id": None
                }

        return create_support_ticket

    def _check_ticket_status_tool(self):
        """Create an AI function for checking ticket status."""

        @ai_function
        async def check_ticket_status(ticket_id: str) -> Dict[str, Any]:
            """
            Check the status of an existing support ticket.

            Args:
                ticket_id: The ticket ID to check

            Returns:
                Current ticket status and details
            """
            if not all([self.partner_center_endpoint, self.tenant_id, self.client_id, self.client_secret]):
                return {
                    "success": False,
                    "error": "Partner Center API is not configured"
                }

            try:
                # Get access token if needed
                if not self._access_token:
                    await self._get_access_token()

                headers = {
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                }

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.partner_center_endpoint}/v1/tickets/{ticket_id}",
                        headers=headers,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    
                    ticket = response.json()
                    return {
                        "success": True,
                        "ticket_id": ticket.get("ticket_id"),
                        "status": ticket.get("status"),
                        "title": ticket.get("title"),
                        "priority": ticket.get("priority"),
                        "last_updated": ticket.get("last_updated"),
                    }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to check ticket status: {str(e)}"
                }

        return check_ticket_status

    async def _get_access_token(self):
        """Get OAuth access token for Partner Center API."""
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://api.partnercenter.microsoft.com/.default",
                "grant_type": "client_credentials",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, timeout=30.0)
                response.raise_for_status()
                
                token_response = response.json()
                self._access_token = token_response.get("access_token")

        except Exception:
            # Avoid logging sensitive authentication details
            self._access_token = None

    def get_agent(self):
        """Return the configured agent instance."""
        return self.agent


def create_ticket_agent(
    partner_center_endpoint: Optional[str] = None,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
):
    """
    Factory function to create and return a Ticket Agent.

    Args:
        partner_center_endpoint: Microsoft Partner Center API endpoint
        tenant_id: Azure AD tenant ID
        client_id: Azure AD application client ID
        client_secret: Azure AD application client secret

    Returns:
        Configured agent for ticket management
    """
    ticket = TicketAgent(
        partner_center_endpoint=partner_center_endpoint,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    return ticket.get_agent()
