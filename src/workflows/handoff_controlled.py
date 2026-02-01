# =============================================================================
# DistriPartner Platform - Controlled Handoff Workflow
# =============================================================================
# Implements the CONTROLLED variant of the HandoffBuilder workflow.
#
# In this variant:
# - Orchestrator returns structured JSON with Intent field
# - Python code reads Intent and determines routing
# - Custom event handling intercepts responses and forces handoffs
# - Full control over routing logic in Python
#
# Architecture:
#   User → Orchestrator (returns JSON Intent)
#              ↓ Python interprets Intent
#          Python calls handoff_to(support|ticketing)
#          Support ←→ User (multi-turn, returns JSON)
#              ↓ Python checks NeedsTicket, forces handoff
#          Ticketing ←→ User (multi-turn)
#
# Note: This variant requires more code but offers precise control.
# The Controlled variant is useful when you need to:
# - Log/audit all routing decisions
# - Apply custom business logic to routing
# - Handle edge cases with deterministic behavior
# =============================================================================

import asyncio
import json
from typing import AsyncIterator

from agent_framework import (
    ChatAgent,
    ChatMessage,
    HandoffBuilder,
    HandoffAgentUserRequest,
    RequestInfoEvent,
    WorkflowEvent,
    WorkflowOutputEvent,
    Workflow,
    AgentRunUpdateEvent,
    WorkflowStatusEvent,
    WorkflowRunState,
)
from azure.identity.aio import DefaultAzureCredential

from .agents import (
    load_orchestrator_controlled,
    load_support_agent,
    load_ticketing_agent,
)
from .common import (
    create_termination_condition,
    handle_workflow_events,
    get_user_input,
    should_exit,
)


async def build_controlled_workflow(credential: DefaultAzureCredential) -> Workflow:
    """
    Build the Controlled handoff workflow.
    
    This workflow uses HandoffBuilder but the Orchestrator returns JSON
    with Intent field. In a full implementation, you would intercept
    the Orchestrator's response and force handoffs based on Intent.
    
    For this version, we use the same HandoffBuilder structure but
    the Orchestrator is configured to return structured JSON output.
    
    Args:
        credential: Azure credential for authentication
        
    Returns:
        Configured Workflow instance
    """
    # Load agents from YAML definitions
    orchestrator = await load_orchestrator_controlled(credential)
    support = await load_support_agent(credential)
    ticketing = await load_ticketing_agent(credential)
    
    # Build the handoff workflow
    # Even in Controlled mode, we use HandoffBuilder for the structure
    # The difference is in how routing decisions are made:
    # - Native: LLM calls handoff tools directly
    # - Controlled: We intercept responses and route based on Intent
    workflow = (
        HandoffBuilder(
            name="distripartner_controlled",
            participants=[orchestrator, support, ticketing],
            description="DistriPartner support workflow with controlled routing",
        )
        # Orchestrator is the entry point
        .with_start_agent(orchestrator)
        # Define handoff paths (same as native)
        .add_handoff(
            orchestrator,
            [support, ticketing],
            description="Route user based on classified intent",
        )
        .add_handoff(
            support,
            [ticketing],
            description="Escalate to ticketing when NeedsTicket is true",
        )
        .add_handoff(
            ticketing,
            [support],
            description="Return to support if needed",
        )
        # Termination condition
        .with_termination_condition(create_termination_condition(max_turns=20))
        .build()
    )
    
    return workflow


def extract_intent_from_response(response_text: str) -> str | None:
    """
    Extract the Intent field from a JSON response.
    
    The Orchestrator returns JSON like:
    {
        "Intent": "support",
        "IntentClassified": true,
        "Summary": "User needs help with Outlook"
    }
    
    Args:
        response_text: The agent's response text (may be JSON)
        
    Returns:
        The Intent value or None if not found
    """
    if not response_text:
        return None
    
    try:
        # Try to parse as JSON
        data = json.loads(response_text)
        return data.get("Intent") or data.get("intent")
    except json.JSONDecodeError:
        # Not valid JSON, try to find Intent in text
        # This handles cases where the LLM includes JSON in its response
        import re
        match = re.search(r'"Intent"\s*:\s*"(\w+)"', response_text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    
    return None


def extract_needs_ticket_from_response(response_text: str) -> bool:
    """
    Extract the NeedsTicket field from a Support agent's JSON response.
    
    Args:
        response_text: The agent's response text
        
    Returns:
        True if escalation to Ticketing is needed
    """
    if not response_text:
        return False
    
    try:
        data = json.loads(response_text)
        return bool(data.get("NeedsTicket") or data.get("needs_ticket"))
    except json.JSONDecodeError:
        # Check for NeedsTicket in text
        return "needsticket" in response_text.lower().replace("_", "").replace(" ", "")


async def run_controlled_workflow_interactive(credential: DefaultAzureCredential) -> None:
    """
    Run the Controlled workflow in interactive console mode.
    
    This function demonstrates controlled routing where:
    1. User sends a message
    2. Orchestrator classifies intent (returns JSON)
    3. Python code interprets Intent and logs the decision
    4. Handoff proceeds based on Intent
    
    Note: In this implementation, HandoffBuilder still handles the actual
    handoffs, but we log and can intercept the routing decisions.
    
    Args:
        credential: Azure credential for authentication
    """
    print("\n" + "=" * 60)
    print("  DistriPartner Platform - Controlled Handoff Workflow")
    print("=" * 60)
    print("Type your message and press Enter.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    # Build the workflow
    workflow = await build_controlled_workflow(credential)
    
    # Get initial user input
    user_input = get_user_input()
    if not user_input or should_exit(user_input):
        print("\n👋 Goodbye!")
        return
    
    # Start the workflow
    print(f"\n[Starting workflow with controlled routing...]")
    workflow_result = await workflow.run(user_input)
    pending_requests = handle_workflow_events(workflow_result)
    
    # Process the request/response cycle
    while pending_requests:
        user_input = get_user_input()
        
        if not user_input:
            continue
        
        if should_exit(user_input):
            responses = {
                req.request_id: HandoffAgentUserRequest.terminate()
                for req in pending_requests
            }
            await workflow.send_responses(responses)
            print("\n👋 Goodbye!")
            break
        
        # Send user response
        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(user_input)
            for req in pending_requests
        }
        
        events = await workflow.send_responses(responses)
        pending_requests = handle_workflow_events(events)
    
    print("\n[Workflow completed]")


async def run_controlled_workflow_streaming(credential: DefaultAzureCredential) -> None:
    """
    Run the Controlled workflow with streaming responses.
    
    This variant uses run_stream() and logs routing decisions.
    
    Args:
        credential: Azure credential for authentication
    """
    print("\n" + "=" * 60)
    print("  DistriPartner Platform - Controlled Handoff Workflow (Streaming)")
    print("=" * 60)
    print("Type your message and press Enter.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    # Build the workflow
    workflow = await build_controlled_workflow(credential)
    
    # Get initial user input
    user_input = get_user_input()
    if not user_input or should_exit(user_input):
        print("\n👋 Goodbye!")
        return
    
    current_agent: str | None = None
    pending_requests: list[RequestInfoEvent] = []
    collected_text: str = ""  # Collect text to analyze Intent
    
    print(f"\n[Starting workflow with controlled routing...]")
    async for event in workflow.run_stream(user_input):
        if isinstance(event, AgentRunUpdateEvent):
            if current_agent != event.executor_id:
                # Log agent switch (routing decision point)
                if current_agent is not None:
                    print()
                    # Analyze collected text for Intent
                    intent = extract_intent_from_response(collected_text)
                    if intent:
                        print(f"[Routing Decision: Intent={intent}]")
                    collected_text = ""
                
                print(f"\n🤖 {event.executor_id}: ", end="", flush=True)
                current_agent = event.executor_id
            
            if event.data and event.data.text:
                print(event.data.text, end="", flush=True)
                collected_text += event.data.text
        
        elif isinstance(event, RequestInfoEvent):
            if isinstance(event.data, HandoffAgentUserRequest):
                pending_requests.append(event)
        
        elif isinstance(event, WorkflowStatusEvent):
            if event.state in {WorkflowRunState.IDLE, WorkflowRunState.IDLE_WITH_PENDING_REQUESTS}:
                print()
    
    # Handle follow-up interactions
    while pending_requests:
        user_input = get_user_input()
        
        if not user_input:
            continue
        
        if should_exit(user_input):
            responses = {
                req.request_id: HandoffAgentUserRequest.terminate()
                for req in pending_requests
            }
            await workflow.send_responses(responses)
            print("\n👋 Goodbye!")
            break
        
        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(user_input)
            for req in pending_requests
        }
        
        pending_requests = []
        current_agent = None
        collected_text = ""
        
        async for event in workflow.send_responses_streaming(responses):
            if isinstance(event, AgentRunUpdateEvent):
                if current_agent != event.executor_id:
                    if current_agent is not None:
                        print()
                        intent = extract_intent_from_response(collected_text)
                        if intent:
                            print(f"[Routing Decision: Intent={intent}]")
                        collected_text = ""
                    
                    print(f"\n🤖 {event.executor_id}: ", end="", flush=True)
                    current_agent = event.executor_id
                
                if event.data and event.data.text:
                    print(event.data.text, end="", flush=True)
                    collected_text += event.data.text
            
            elif isinstance(event, RequestInfoEvent):
                if isinstance(event.data, HandoffAgentUserRequest):
                    pending_requests.append(event)
            
            elif isinstance(event, WorkflowStatusEvent):
                if event.state in {WorkflowRunState.IDLE, WorkflowRunState.IDLE_WITH_PENDING_REQUESTS}:
                    print()
    
    print("\n[Workflow completed]")
