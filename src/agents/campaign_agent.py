"""
Campaign Agent for the Microsoft Agent Framework workflow.

This agent handles campaign execution and management actions on behalf
of distributors.
"""

from agent_framework import ChatAgent, ai_function
from typing import Any, Dict, List, Optional
import os
from datetime import datetime


class CampaignAgent:
    """
    Campaign Agent that executes marketing and operational actions for distributors.
    """

    def __init__(self):
        """Initialize the Campaign Agent."""
        # Create the campaign agent
        self.agent = ChatAgent(
            name="campaign",
            model="azure-openai",
            instructions=self._get_instructions(),
            tools=self._setup_tools(),
        )

    def _get_instructions(self) -> str:
        """Get the system instructions for the campaign agent."""
        return """You are the Campaign Agent for a Microsoft Partner support system.

Your role is to execute and manage marketing campaigns and operational actions on behalf of distributors.

Capabilities:
- Create and launch marketing campaigns
- Update existing campaign parameters
- Retrieve campaign performance metrics
- Schedule campaign activities
- Manage campaign budgets and resources
- Execute distributor-specific actions

Guidelines:
- Validate all campaign parameters before execution
- Confirm actions with detailed summaries before proceeding
- Provide clear status updates and confirmations
- Handle errors gracefully with helpful messages
- Ensure compliance with campaign policies
- Track and report campaign performance

Campaign types:
- Email marketing campaigns
- Promotional campaigns
- Partner engagement campaigns
- Product launch campaigns
- Training and enablement campaigns

When you've completed the campaign action, let them know they'll be returned to the orchestrator."""

    def _setup_tools(self) -> list:
        """Set up tools for the campaign agent."""
        return [
            self._create_campaign_tool(),
            self._update_campaign_tool(),
            self._get_campaign_status_tool(),
            self._execute_distributor_action_tool(),
        ]

    def _create_campaign_tool(self):
        """Create an AI function for creating campaigns."""

        @ai_function
        async def create_campaign(
            campaign_name: str,
            campaign_type: str,
            target_audience: str,
            start_date: str,
            end_date: str,
            budget: Optional[float] = None,
            description: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Create a new marketing campaign.

            Args:
                campaign_name: Name of the campaign
                campaign_type: Type of campaign (email, promotional, partner, product, training)
                target_audience: Description of target audience
                start_date: Campaign start date (ISO format)
                end_date: Campaign end date (ISO format)
                budget: Optional budget allocation
                description: Optional campaign description

            Returns:
                Campaign creation result with campaign ID
            """
            try:
                # Validate dates
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                if end <= start:
                    return {
                        "success": False,
                        "error": "End date must be after start date",
                        "campaign_id": None
                    }

                # Create campaign data
                campaign_data = {
                    "campaign_id": f"CAMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "name": campaign_name,
                    "type": campaign_type,
                    "target_audience": target_audience,
                    "start_date": start_date,
                    "end_date": end_date,
                    "budget": budget,
                    "description": description,
                    "status": "Created",
                    "created_at": datetime.utcnow().isoformat(),
                }

                # In a real implementation, this would call an API or database
                # For now, we'll simulate success
                return {
                    "success": True,
                    "campaign_id": campaign_data["campaign_id"],
                    "status": campaign_data["status"],
                    "message": f"Campaign '{campaign_name}' created successfully",
                    "details": campaign_data
                }

            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid date format: {str(e)}",
                    "campaign_id": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to create campaign: {str(e)}",
                    "campaign_id": None
                }

        return create_campaign

    def _update_campaign_tool(self):
        """Create an AI function for updating campaigns."""

        @ai_function
        async def update_campaign(
            campaign_id: str,
            status: Optional[str] = None,
            budget: Optional[float] = None,
            end_date: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Update an existing campaign.

            Args:
                campaign_id: ID of the campaign to update
                status: New status (Created, Active, Paused, Completed, Cancelled)
                budget: Updated budget allocation
                end_date: Updated end date (ISO format)

            Returns:
                Campaign update result
            """
            try:
                updates = {}
                
                if status:
                    valid_statuses = ["Created", "Active", "Paused", "Completed", "Cancelled"]
                    if status not in valid_statuses:
                        return {
                            "success": False,
                            "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                        }
                    updates["status"] = status

                if budget is not None:
                    if budget < 0:
                        return {
                            "success": False,
                            "error": "Budget must be non-negative"
                        }
                    updates["budget"] = budget

                if end_date:
                    # Validate date format
                    datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    updates["end_date"] = end_date

                updates["last_modified"] = datetime.utcnow().isoformat()

                # In a real implementation, this would update via API or database
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "message": "Campaign updated successfully",
                    "updates": updates
                }

            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid date format: {str(e)}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to update campaign: {str(e)}"
                }

        return update_campaign

    def _get_campaign_status_tool(self):
        """Create an AI function for retrieving campaign status."""

        @ai_function
        async def get_campaign_status(campaign_id: str) -> Dict[str, Any]:
            """
            Get the current status and metrics for a campaign.

            Args:
                campaign_id: ID of the campaign

            Returns:
                Campaign status and performance metrics
            """
            try:
                # In a real implementation, this would query the database
                # For now, we'll simulate a response
                campaign_status = {
                    "campaign_id": campaign_id,
                    "status": "Active",
                    "metrics": {
                        "impressions": 15000,
                        "clicks": 450,
                        "conversions": 23,
                        "engagement_rate": "3.0%",
                        "conversion_rate": "5.1%",
                    },
                    "budget_used": 750.00,
                    "budget_remaining": 250.00,
                    "days_remaining": 7
                }

                return {
                    "success": True,
                    "campaign": campaign_status
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to get campaign status: {str(e)}"
                }

        return get_campaign_status

    def _execute_distributor_action_tool(self):
        """Create an AI function for executing distributor-specific actions."""

        @ai_function
        async def execute_distributor_action(
            distributor_id: str,
            action_type: str,
            parameters: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            Execute a specific action on behalf of a distributor.

            Args:
                distributor_id: ID of the distributor
                action_type: Type of action to execute
                parameters: Action-specific parameters

            Returns:
                Action execution result
            """
            try:
                valid_actions = [
                    "send_notification",
                    "update_inventory",
                    "generate_report",
                    "schedule_meeting",
                    "update_pricing"
                ]

                if action_type not in valid_actions:
                    return {
                        "success": False,
                        "error": f"Invalid action type. Must be one of: {', '.join(valid_actions)}"
                    }

                # Execute the action based on type
                action_result = {
                    "action_id": f"ACT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "distributor_id": distributor_id,
                    "action_type": action_type,
                    "parameters": parameters,
                    "status": "Completed",
                    "executed_at": datetime.utcnow().isoformat()
                }

                return {
                    "success": True,
                    "message": f"Action '{action_type}' executed successfully",
                    "result": action_result
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to execute action: {str(e)}"
                }

        return execute_distributor_action

    def get_agent(self) -> ChatAgent:
        """Return the configured ChatAgent instance."""
        return self.agent


def create_campaign_agent() -> ChatAgent:
    """
    Factory function to create and return a Campaign Agent.

    Returns:
        Configured ChatAgent for campaign management
    """
    campaign = CampaignAgent()
    return campaign.get_agent()
