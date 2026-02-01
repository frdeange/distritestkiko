# =============================================================================
# DistriPartner Platform - Pydantic Schemas
# =============================================================================
# Data models for structured outputs from agents.
# These schemas define the expected response formats for workflow routing.
# =============================================================================

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Intent(str, Enum):
    """User intent classification for routing decisions."""
    
    SUPPORT = "support"
    TICKETING = "ticketing"
    CHITCHAT = "chitchat"


class OrchestratorResponse(BaseModel):
    """
    Structured response from the Orchestrator agent.
    
    Used in the Controlled variant to determine routing based on
    the Intent field. The Native variant uses tool calls instead.
    """
    
    intent: Intent = Field(
        ...,
        description=(
            "The classified user intent. Must be one of: "
            "'support' (technical questions, troubleshooting), "
            "'ticketing' (explicit ticket requests), or "
            "'chitchat' (greetings, small talk)."
        ),
    )
    
    intent_classified: bool = Field(
        default=True,
        description=(
            "Whether the intent was clearly classified. "
            "Set to false only if the message is completely unintelligible."
        ),
    )
    
    summary: Optional[str] = Field(
        default=None,
        description="Brief summary of the user's request for handoff context.",
    )


class SupportResponse(BaseModel):
    """
    Structured response from the Support agent.
    
    Indicates whether the issue was resolved or needs escalation to Ticketing.
    """
    
    is_resolved: bool = Field(
        ...,
        description=(
            "Whether the user's issue has been fully resolved. "
            "Set to true when the user confirms satisfaction or the issue is solved."
        ),
    )
    
    needs_ticket: bool = Field(
        ...,
        description=(
            "Whether the issue requires escalation to the Ticketing agent. "
            "Set to true when: issue cannot be resolved with documentation, "
            "user explicitly requests a ticket, multiple attempts failed, "
            "or specialist review is needed."
        ),
    )
    
    resolution_summary: str = Field(
        ...,
        description=(
            "Summary of the conversation and any troubleshooting steps attempted. "
            "Include what was tried and the outcome. Helps Ticketing if escalated."
        ),
    )
    
    category: Optional[str] = Field(
        default=None,
        description="The category of the issue: 'azure', 'm365', 'dynamics', 'general'.",
    )


class TicketingResponse(BaseModel):
    """
    Structured response from the Ticketing agent.
    
    Contains ticket creation status and details.
    """
    
    ticket_id: Optional[str] = Field(
        default=None,
        description="The generated ticket ID in format TKT-YYYYMMDD-XXXX.",
    )
    
    status: str = Field(
        default="pending",
        description=(
            "Current status of ticket creation: "
            "'pending' (gathering info), 'created' (ticket saved), "
            "'email_sent' (notification sent), 'error' (creation failed)."
        ),
    )
    
    next_steps: Optional[str] = Field(
        default=None,
        description="What the user should expect or do next.",
    )
    
    requires_more_info: bool = Field(
        default=False,
        description="Whether additional information is needed from the user.",
    )
