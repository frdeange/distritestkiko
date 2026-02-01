# =============================================================================
# DistriPartner Platform - Native Handoff Workflow
# =============================================================================
# Implements the NATIVE variant of the HandoffBuilder workflow.
#
# In this variant:
# - HandoffBuilder auto-generates handoff tools (handoff_to_support, etc.)
# - Orchestrator agent uses these tools naturally via LLM decisions
# - Routing is decentralized - agents decide handoffs via tool calls
# - Support agent can escalate to Ticketing via handoff_to_ticketing
#
# Architecture:
#   User → Orchestrator (decides via tool call)
#              ↓ handoff_to_support() or handoff_to_ticketing()
#          Support ←→ User (multi-turn)
#              ↓ handoff_to_ticketing() (if NeedsTicket)
#          Ticketing ←→ User (multi-turn)
# =============================================================================

import asyncio
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
)
from azure.identity.aio import DefaultAzureCredential

from .agents import (
    load_orchestrator_native,
    load_support_agent,
    load_ticketing_agent,
)
from .common import (
    create_termination_condition,
    handle_workflow_events,
    get_user_input,
    should_exit,
)


async def build_native_workflow(credential: DefaultAzureCredential) -> Workflow:
    """
    Build the Native handoff workflow.
    
    This workflow uses HandoffBuilder with auto-generated handoff tools.
    The Orchestrator agent decides routing by calling handoff_to_support()
    or handoff_to_ticketing() tools.
    
    Args:
        credential: Azure credential for authentication
        
    Returns:
        Configured Workflow instance
    """
    # Load agents from YAML definitions
    orchestrator = await load_orchestrator_native(credential)
    support = await load_support_agent(credential)
    ticketing = await load_ticketing_agent(credential)
    
    # Build the handoff workflow
    # HandoffBuilder auto-creates handoff tools based on add_handoff() calls
    workflow = (
        HandoffBuilder(
            name="distripartner_native",
            participants=[orchestrator, support, ticketing],
            description="DistriPartner support workflow with native handoff tools",
        )
        # Orchestrator is the entry point for all conversations
        .with_start_agent(orchestrator)
        # Define handoff paths:
        # - Orchestrator can hand off to Support or Ticketing
        .add_handoff(
            orchestrator,
            [support, ticketing],
            description="Route user to appropriate specialist agent",
        )
        # - Support can hand off to Ticketing (escalation)
        .add_handoff(
            support,
            [ticketing],
            description="Escalate to ticketing when issue cannot be resolved",
        )
        # - Ticketing can hand off back to Support (rare, but possible)
        .add_handoff(
            ticketing,
            [support],
            description="Return to support for additional troubleshooting",
        )
        # Termination condition: natural conversation end or max turns
        .with_termination_condition(create_termination_condition(max_turns=20))
        .build()
    )
    
    return workflow


async def run_native_workflow_interactive(credential: DefaultAzureCredential) -> None:
    """
    Run the Native workflow in interactive console mode.
    
    This function demonstrates the human-in-the-loop pattern where:
    1. User sends a message
    2. Workflow processes and agents respond
    3. Workflow pauses for user input when needed
    4. Loop continues until termination condition
    
    Args:
        credential: Azure credential for authentication
    """
    print("\n" + "=" * 60)
    print("  DistriPartner Platform - Native Handoff Workflow")
    print("=" * 60)
    print("Type your message and press Enter.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    # Build the workflow
    workflow = await build_native_workflow(credential)
    
    # Get initial user input
    user_input = get_user_input()
    if not user_input or should_exit(user_input):
        print("\n👋 Goodbye!")
        return
    
    # Start the workflow with initial message
    print(f"\n[Starting workflow...]")
    workflow_result = await workflow.run(user_input)
    pending_requests = handle_workflow_events(workflow_result)
    
    # Process the request/response cycle
    while pending_requests:
        # Get user input
        user_input = get_user_input()
        
        if not user_input:
            continue
        
        if should_exit(user_input):
            # Terminate the workflow gracefully
            responses = {
                req.request_id: HandoffAgentUserRequest.terminate()
                for req in pending_requests
            }
            await workflow.send_responses(responses)
            print("\n👋 Goodbye!")
            break
        
        # Send user response to pending requests
        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(user_input)
            for req in pending_requests
        }
        
        # Get workflow response
        events = await workflow.send_responses(responses)
        pending_requests = handle_workflow_events(events)
    
    print("\n[Workflow completed]")


async def run_native_workflow_streaming(credential: DefaultAzureCredential) -> None:
    """
    Run the Native workflow with streaming responses.
    
    This variant uses run_stream() for real-time response display.
    
    Args:
        credential: Azure credential for authentication
    """
    from agent_framework import AgentRunUpdateEvent, WorkflowStatusEvent, WorkflowRunState
    
    print("\n" + "=" * 60)
    print("  DistriPartner Platform - Native Handoff Workflow (Streaming)")
    print("=" * 60)
    print("Type your message and press Enter.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    # Build the workflow
    workflow = await build_native_workflow(credential)
    
    # Get initial user input
    user_input = get_user_input()
    if not user_input or should_exit(user_input):
        print("\n👋 Goodbye!")
        return
    
    current_agent: str | None = None
    pending_requests: list[RequestInfoEvent] = []
    
    # Start the workflow with streaming
    print(f"\n[Starting workflow...]")
    async for event in workflow.run_stream(user_input):
        if isinstance(event, AgentRunUpdateEvent):
            # Print agent name header when switching agents
            if current_agent != event.executor_id:
                if current_agent is not None:
                    print()  # New line after previous agent
                print(f"\n🤖 {event.executor_id}: ", end="", flush=True)
                current_agent = event.executor_id
            # Print streaming text
            if event.data and event.data.text:
                print(event.data.text, end="", flush=True)
        
        elif isinstance(event, RequestInfoEvent):
            if isinstance(event.data, HandoffAgentUserRequest):
                pending_requests.append(event)
        
        elif isinstance(event, WorkflowStatusEvent):
            if event.state in {WorkflowRunState.IDLE, WorkflowRunState.IDLE_WITH_PENDING_REQUESTS}:
                print()  # New line after streaming
    
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
        
        # Send user response
        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(user_input)
            for req in pending_requests
        }
        
        pending_requests = []
        current_agent = None
        
        async for event in workflow.send_responses_streaming(responses):
            if isinstance(event, AgentRunUpdateEvent):
                if current_agent != event.executor_id:
                    if current_agent is not None:
                        print()
                    print(f"\n🤖 {event.executor_id}: ", end="", flush=True)
                    current_agent = event.executor_id
                if event.data and event.data.text:
                    print(event.data.text, end="", flush=True)
            
            elif isinstance(event, RequestInfoEvent):
                if isinstance(event.data, HandoffAgentUserRequest):
                    pending_requests.append(event)
            
            elif isinstance(event, WorkflowStatusEvent):
                if event.state in {WorkflowRunState.IDLE, WorkflowRunState.IDLE_WITH_PENDING_REQUESTS}:
                    print()
    
    print("\n[Workflow completed]")
