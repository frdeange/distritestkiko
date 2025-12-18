"""
Notification Agent for the Microsoft Agent Framework workflow.

This is a skeleton implementation for future development.
The agent will send email notifications using Azure Communication Service.
"""

from agent_framework import ai_function
from typing import Any, Dict, List, Optional
import os
from .utils import create_azure_ai_client


class NotificationAgent:
    """
    Notification Agent (Skeleton) that will send emails based on events.
    
    NOTE: This is a skeleton implementation for future development.
    """

    def __init__(
        self,
        communication_connection_string: Optional[str] = None,
        sender_email: Optional[str] = None,
    ):
        """
        Initialize the Notification Agent.

        Args:
            communication_connection_string: Azure Communication Service connection string
            sender_email: Sender email address
        """
        self.communication_connection_string = communication_connection_string or os.getenv(
            "AZURE_COMMUNICATION_CONNECTION_STRING"
        )
        self.sender_email = sender_email or os.getenv("AZURE_COMMUNICATION_SENDER_EMAIL")

        # Create the notification agent
        chat_client = create_azure_ai_client()
        self.agent = chat_client.create_agent(
            name="notification",
            instructions=self._get_instructions(),
            tools=self._setup_tools(),
        )

    def _get_instructions(self) -> str:
        """Get the system instructions for the notification agent."""
        return """You are the Notification Agent for a Microsoft Partner support system.

IMPORTANT: This is a skeleton implementation for future development.

Your planned role is to send email notifications based on various events:
- Ticket creation confirmations
- Campaign status updates
- System alerts and notifications
- User-requested notifications

Currently, this agent is not fully implemented and will be enhanced in future iterations.

When users interact with you, let them know this functionality is planned for a future release."""

    def _setup_tools(self) -> list:
        """Set up tools for the notification agent."""
        return [
            self._create_send_email_tool(),
        ]

    def _create_send_email_tool(self):
        """Create an AI function for sending emails (skeleton implementation)."""

        @ai_function
        async def send_email_notification(
            recipient_email: str,
            subject: str,
            body: str,
            is_html: bool = False
        ) -> Dict[str, Any]:
            """
            Send an email notification (Skeleton - Not fully implemented).

            Args:
                recipient_email: Recipient email address
                subject: Email subject
                body: Email body content
                is_html: Whether the body is HTML formatted

            Returns:
                Email sending result (currently simulated)
            """
            # TODO: Implement actual email sending using Azure Communication Service
            # This is a skeleton implementation
            
            if not self.communication_connection_string or not self.sender_email:
                return {
                    "success": False,
                    "error": "Azure Communication Service is not configured",
                    "message_id": None,
                    "note": "This is a skeleton implementation. Email functionality will be added in future releases."
                }

            # Simulate email sending
            return {
                "success": True,
                "message_id": "SIMULATED-MESSAGE-ID",
                "recipient": recipient_email,
                "subject": subject,
                "note": "This is a skeleton implementation. No actual email was sent. This functionality will be fully implemented in future releases."
            }

        return send_email_notification

    def get_agent(self):
        """Return the configured agent instance."""
        return self.agent


def create_notification_agent(
    communication_connection_string: Optional[str] = None,
    sender_email: Optional[str] = None,
):
    """
    Factory function to create and return a Notification Agent (Skeleton).

    Args:
        communication_connection_string: Azure Communication Service connection string
        sender_email: Sender email address

    Returns:
        Configured agent for notifications (skeleton implementation)
    """
    notification = NotificationAgent(
        communication_connection_string=communication_connection_string,
        sender_email=sender_email,
    )
    return notification.get_agent()
