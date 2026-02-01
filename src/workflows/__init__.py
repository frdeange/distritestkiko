# =============================================================================
# DistriPartner Platform - Workflow Module
# =============================================================================
# Programmatic workflow implementation using Microsoft Agent Framework's
# HandoffBuilder pattern. Replaces the declarative YAML workflow.
# =============================================================================

from .agents import (
    load_orchestrator_native,
    load_orchestrator_controlled,
    load_support_agent,
    load_ticketing_agent,
    get_agents_dir,
)

from .common import (
    create_termination_condition,
    handle_workflow_events,
    print_agent_response,
)

__all__ = [
    # Agent loading
    "load_orchestrator_native",
    "load_orchestrator_controlled",
    "load_support_agent",
    "load_ticketing_agent",
    "get_agents_dir",
    # Common utilities
    "create_termination_condition",
    "handle_workflow_events",
    "print_agent_response",
]
