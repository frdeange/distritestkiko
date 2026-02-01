# =============================================================================
# DistriPartner Platform - Common Workflow Utilities
# =============================================================================
# Shared helper functions for workflow execution, event handling,
# and termination conditions.
# =============================================================================

from typing import Callable, Any
from collections.abc import Sequence

from agent_framework import (
    AgentResponse,
    ChatMessage,
    WorkflowEvent,
    WorkflowOutputEvent,
    WorkflowStatusEvent,
    WorkflowRunState,
    AgentRunEvent,
    AgentRunUpdateEvent,
    RequestInfoEvent,
    HandoffSentEvent,
    HandoffAgentUserRequest,
)


def create_termination_condition(
    max_turns: int = 20,
    end_phrases: Sequence[str] | None = None,
) -> Callable[[list[ChatMessage]], bool]:
    """
    Create a termination condition for the handoff workflow.
    
    The workflow terminates when:
    1. Max turns are reached, OR
    2. The last message contains an end phrase (e.g., "you're welcome")
    
    Args:
        max_turns: Maximum number of turns before termination
        end_phrases: Phrases that indicate natural conversation end
        
    Returns:
        Callable that evaluates termination condition
    """
    if end_phrases is None:
        end_phrases = [
            "welcome",  # "you're welcome"
            "goodbye",
            "have a great day",
            "anything else",
            "is there anything else",
        ]
    
    def condition(conversation: list[ChatMessage]) -> bool:
        # Check max turns
        if len(conversation) >= max_turns:
            return True
        
        # Check end phrases in last message
        if conversation:
            last_text = (conversation[-1].text or "").lower()
            for phrase in end_phrases:
                if phrase in last_text:
                    return True
        
        return False
    
    return condition


def handle_workflow_events(
    events: list[WorkflowEvent],
    verbose: bool = True,
) -> list[RequestInfoEvent]:
    """
    Process workflow events and extract pending user input requests.
    
    This function handles various event types from the workflow:
    - AgentRunEvent: Agent responses (non-streaming)
    - AgentRunUpdateEvent: Streaming updates
    - HandoffSentEvent: Handoff notifications
    - WorkflowStatusEvent: State changes
    - WorkflowOutputEvent: Final conversation snapshot
    - RequestInfoEvent: Requests for user input
    
    Args:
        events: List of workflow events to process
        verbose: Whether to print event details
        
    Returns:
        List of pending RequestInfoEvent requiring user input
    """
    pending_requests: list[RequestInfoEvent] = []
    
    for event in events:
        if isinstance(event, AgentRunEvent):
            if verbose and event.data:
                print_agent_response(event.data, event.executor_id)
        
        elif isinstance(event, AgentRunUpdateEvent):
            # Streaming update - print incrementally
            if verbose and event.data and event.data.text:
                print(event.data.text, end="", flush=True)
        
        elif isinstance(event, HandoffSentEvent):
            if verbose:
                print(f"\n[Handoff: {event.source} → {event.target}]")
        
        elif isinstance(event, WorkflowStatusEvent):
            if verbose and event.state in {
                WorkflowRunState.IDLE,
                WorkflowRunState.IDLE_WITH_PENDING_REQUESTS,
            }:
                print(f"\n[Workflow Status: {event.state.name}]")
        
        elif isinstance(event, WorkflowOutputEvent):
            if verbose:
                print("\n=== Workflow Complete ===")
        
        elif isinstance(event, RequestInfoEvent):
            if isinstance(event.data, HandoffAgentUserRequest):
                pending_requests.append(event)
                if verbose:
                    print_handoff_user_request(event.data)
    
    return pending_requests


def print_agent_response(response: AgentResponse, agent_name: str | None = None) -> None:
    """
    Print an agent's response in a formatted way.
    
    Args:
        response: The agent response to print
        agent_name: Optional agent name for attribution
    """
    for message in response.messages:
        if message.text:
            speaker = message.author_name or agent_name or message.role.value
            print(f"\n🤖 {speaker}: {message.text}")


def print_handoff_user_request(request: HandoffAgentUserRequest) -> None:
    """
    Print a handoff user request (agent asking for user input).
    
    Args:
        request: The handoff user request to print
    """
    for message in request.agent_response.messages:
        if message.text:
            speaker = message.author_name or message.role.value
            print(f"\n🤖 {speaker}: {message.text}")


def get_user_input(prompt: str = "You: ") -> str:
    """
    Get input from the user via console.
    
    Args:
        prompt: The prompt to display
        
    Returns:
        User's input string
    """
    try:
        return input(f"\n👤 {prompt}").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def should_exit(user_input: str) -> bool:
    """
    Check if user wants to exit the conversation.
    
    Args:
        user_input: The user's input string
        
    Returns:
        True if user wants to exit
    """
    exit_commands = {"quit", "exit", "q", "bye", "goodbye"}
    return user_input.lower() in exit_commands


def format_conversation_history(messages: list[ChatMessage]) -> str:
    """
    Format a conversation history for display.
    
    Args:
        messages: List of chat messages
        
    Returns:
        Formatted string representation
    """
    lines = []
    for msg in messages:
        speaker = msg.author_name or msg.role.value
        text = msg.text or "[no text]"
        lines.append(f"- {speaker}: {text}")
    return "\n".join(lines)
