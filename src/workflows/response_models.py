# =============================================================================
# DistriPartner Platform - Pydantic Response Models
# =============================================================================
# Structured output models used as response_format for agents in the
# declarative workflow. These models enable the workflow YAML to evaluate
# conditions like =Local.SupportOutput.IsResolved using PowerFx expressions.
#
# Each model corresponds to an agent's structured output schema.
# =============================================================================

from pydantic import BaseModel, Field


class OrchestratorResponse(BaseModel):
    """Structured output from the Orchestrator agent."""

    Response: str = Field(
        description=(
            "The friendly, natural-language message to show the user. "
            "This is what the user sees. Must be warm, helpful, and in "
            "the same language the user used."
        )
    )
    Intent: str = Field(
        description=(
            "The classified user intent. Must be one of: "
            "'support' (technical questions, troubleshooting), "
            "'ticketing' (explicit ticket requests or escalations), "
            "'chitchat' (greetings, small talk, off-topic)"
        )
    )
    IntentClassified: bool = Field(
        description=(
            "Whether the intent was clearly classified. "
            "Set to true when confident about the classification."
        )
    )
    Summary: str = Field(
        default="",
        description="Brief summary of the user's request for handoff context.",
    )


class SupportResponse(BaseModel):
    """Structured output from the Support agent."""

    Response: str = Field(
        description=(
            "The natural-language message to show the user. "
            "Contains troubleshooting guidance, follow-up questions, "
            "or resolution confirmation. Must be in the user's language."
        )
    )
    IsResolved: bool = Field(
        description=(
            "Whether the user's issue has been fully resolved. "
            "Set to true when the user confirms satisfaction or the issue is solved."
        )
    )
    NeedsTicket: bool = Field(
        description=(
            "Whether the issue requires escalation to Ticketing. "
            "Set to true when issue cannot be resolved, user requests a ticket, "
            "or multiple troubleshooting attempts have failed."
        )
    )
    ResolutionSummary: str = Field(
        default="",
        description=(
            "Summary of the conversation and troubleshooting steps attempted. "
            "Helps Ticketing if escalated."
        ),
    )
    Category: str = Field(
        default="general",
        description="Category of the issue: azure, m365, dynamics, or general.",
    )


class TicketingResponse(BaseModel):
    """Structured output from the Ticketing agent."""

    Response: str = Field(
        description=(
            "The natural-language message to show the user. "
            "Provides status updates, asks for missing info, or "
            "confirms ticket creation. Must be in the user's language."
        )
    )
    TicketCreated: bool = Field(
        description=(
            "Whether a support ticket has been successfully created. "
            "Set to true only after the ticket is stored and email is sent."
        )
    )
    TicketId: str = Field(
        default="",
        description="The generated ticket ID in format TKT-YYYYMMDD-XXXX.",
    )
    Status: str = Field(
        description=(
            "Current status of the ticketing process: "
            "'gathering_info', 'creating_ticket', 'completed', or 'failed'."
        )
    )
    Summary: str = Field(
        default="",
        description="Brief summary of the ticket or current conversation state.",
    )
    ProductFamily: str = Field(
        default="",
        description="Classified product family: Azure, M365, or Dynamics.",
    )
    Priority: str = Field(
        default="Medium",
        description="Assigned priority: Critical, High, Medium, or Low.",
    )


class DataGathererResponse(BaseModel):
    """Structured output from the DataGatherer agent (fused Profiler + DataCollector)."""

    # Profile fields
    success: bool = Field(
        description="Whether the data gathering was successful overall."
    )
    error: str | None = Field(
        default=None,
        description="Error message if retrieval failed, null otherwise.",
    )
    userId: str = Field(default="", description="Unique user identifier from EntraID.")
    userPrincipalName: str = Field(default="", description="User principal name (UPN).")
    email: str = Field(default="", description="Primary email address.")
    displayName: str = Field(default="", description="User's display name.")
    jobTitle: str = Field(default="", description="User's job title.")
    department: str = Field(default="", description="User's department.")
    organization: str = Field(default="", description="User's organization/company.")
    managerId: str = Field(default="", description="Manager's user ID.")
    managerEmail: str = Field(default="", description="Manager's email address.")
    phone: str = Field(default="", description="User's phone number.")
    accountEnabled: bool = Field(default=True, description="Whether account is enabled.")

    # Subscription fields
    queryTimestamp: str = Field(
        default="",
        description="ISO timestamp of when the query was executed.",
    )
    subscriptionId: str = Field(
        default="", description="Primary subscription identifier."
    )
    subscriptionName: str = Field(
        default="", description="Human-readable subscription name."
    )
    subscriptionStatus: str = Field(
        default="", description="Subscription status (active, suspended, expired)."
    )
    tier: str = Field(default="", description="Subscription tier/plan level.")
    tenantId: str = Field(default="", description="Associated tenant ID.")
    tenantName: str = Field(default="", description="Associated tenant name.")
    domain: str = Field(default="", description="Primary domain for the tenant.")
    region: str = Field(default="", description="Geographic region of the tenant.")


class CommunicationResponse(BaseModel):
    """Structured output from the Communication agent."""

    Response: str = Field(
        default="",
        description=(
            "A brief, human-friendly status message about the email notification. "
            "Example: 'Email notification sent successfully for ticket TKT-20240607-7324.' "
            "This is the text shown to the user. Keep it short and informative."
        ),
    )
    emailSent: bool = Field(
        description="Whether the email notification was successfully sent."
    )
    error: str | None = Field(
        default=None,
        description="Error message if sending failed, null otherwise.",
    )
    recipientCount: int = Field(
        default=0,
        description="Number of recipients the email was sent to.",
    )
