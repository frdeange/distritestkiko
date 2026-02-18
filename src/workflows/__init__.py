# =============================================================================
# DistriPartner Platform - Workflow Module
# =============================================================================
# Declarative workflow implementation using AzureOpenAIResponsesClient
# and WorkflowFactory with YAML-defined routing.
# =============================================================================

from .declarative import (
    create_declarative_workflow,
    run_declarative_workflow_streaming,
    run_declarative_workflow_interactive,
)

from .response_models import (
    OrchestratorResponse,
    SupportResponse,
    TicketingResponse,
    DataGathererResponse,
    CommunicationResponse,
)

__all__ = [
    # Declarative workflow
    "create_declarative_workflow",
    "run_declarative_workflow_streaming",
    "run_declarative_workflow_interactive",
    # Response models
    "OrchestratorResponse",
    "SupportResponse",
    "TicketingResponse",
    "DataGathererResponse",
    "CommunicationResponse",
]
