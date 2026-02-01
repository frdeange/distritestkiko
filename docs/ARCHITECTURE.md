# DistriPartner Platform - Architecture Reference

This document describes the architecture of the DistriPartner Platform, a multi-agent system built with Microsoft Agent Framework using **declarative YAML agent definitions** and **programmatic Python workflows**.

## Table of Contents

- [Overview](#overview)
- [Architecture Decision: Hybrid Approach](#architecture-decision-hybrid-approach)
- [Workflow Architecture](#workflow-architecture)
- [HandoffBuilder Pattern](#handoffbuilder-pattern)
- [Agent Definitions](#agent-definitions)
- [Workflow Variants](#workflow-variants)
- [Adding New Agents](#adding-new-agents)
- [Human-in-the-Loop Pattern](#human-in-the-loop-pattern)
- [Folder Structure](#folder-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

DistriPartner Platform is a customer support system that uses multiple specialized AI agents to handle user requests. The system uses:

- **Declarative YAML** for agent definitions (model, instructions, tools, output schemas)
- **Programmatic Python** for workflow orchestration using `HandoffBuilder`
- **Azure AI Foundry** for LLM capabilities
- **MCP (Model Context Protocol)** for external tool integration

### Key Principles

1. **Hybrid Approach**: YAML for agents, Python for workflows
2. **Separation of Concerns**: Each agent has a specific responsibility
3. **HandoffBuilder Pattern**: Decentralized routing where agents decide handoffs
4. **Human-in-the-Loop**: Workflows support multi-turn conversations

---

## Architecture Decision: Hybrid Approach

### Why Not Fully Declarative Workflows?

The platform initially used fully declarative YAML workflows, but encountered issues:

1. **PowerFx Limitations**: The Python PowerFx wrapper has bugs with nested property access:
   - `Local.OrchestratorResponse.Intent` fails when `OrchestratorResponse` is `None`
   - Error: "Deprecated use of '.'. Please use the 'ShowColumns' function instead."

2. **Debugging Difficulty**: Declarative workflows are hard to debug when issues arise

3. **Limited Flexibility**: Custom routing logic requires PowerFx expressions

### The Hybrid Solution

```
┌───────────────────────────────────────────────────────────┐
│  DECLARATIVE (YAML)            │  PROGRAMMATIC (Python)   │
├───────────────────────────────────────────────────────────┤
│  • Agent definitions            │  • Workflow orchestration │
│  • Model configuration          │  • Routing logic          │
│  • Instructions                 │  • Event handling         │
│  • Tools (MCP, file_search)     │  • Termination conditions │
│  • Output schemas               │  • Human-in-the-loop      │
└───────────────────────────────────────────────────────────┘
```

**Benefits:**
- Agents remain declarative (easy to modify without code changes)
- Workflows are reliable and debuggable
- Full control over routing decisions
- Easier error handling and logging

---

## Workflow Architecture

### Current Implementation: Support Flow

```
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │  (Entry Point)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              │              ▼
     ┌────────────────┐      │     ┌────────────────┐
     │    Support     │◄─────┘     │   Ticketing    │
     │  (L1 Support)  │            │ (Ticket Open)  │
     └───────┬────────┘            └────────────────┘
             │                              ▲
             │ (cannot resolve /            │
             │  needs ticket)               │
             └──────────────────────────────┘
```

### Routing Logic

| From | To | Condition |
|------|-----|-----------|
| Orchestrator | Support | User has technical questions, needs help |
| Orchestrator | Ticketing | User explicitly requests a ticket |
| Support | Ticketing | `NeedsTicket = true` - Cannot resolve, needs escalation |
| Any | End | Termination condition met (e.g., "you're welcome") |

---

## HandoffBuilder Pattern

The `HandoffBuilder` is the core of the programmatic workflow. It creates a workflow where agents can hand off control to each other via tool calls.

### How It Works

1. **HandoffBuilder** automatically creates `handoff_to_*()` tools for each agent
2. When an agent calls `handoff_to_support()`, control transfers to Support
3. The entire conversation history is maintained across handoffs
4. Human-in-the-loop: workflow pauses for user input when needed

### Code Example

```python
from agent_framework import HandoffBuilder

workflow = (
    HandoffBuilder(
        name="distripartner_workflow",
        participants=[orchestrator, support, ticketing],
    )
    .with_start_agent(orchestrator)       # Entry point
    .add_handoff(orchestrator, [support, ticketing])  # Orchestrator can route to these
    .add_handoff(support, [ticketing])    # Support can escalate to Ticketing
    .with_termination_condition(
        lambda conv: "welcome" in conv[-1].text.lower()  # Natural end
    )
    .build()
)
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `participants([...])` | Register all agents in the workflow |
| `with_start_agent(agent)` | Set the entry point agent |
| `add_handoff(source, [targets])` | Define routing paths |
| `with_termination_condition(fn)` | Custom termination logic |
| `build()` | Create the Workflow instance |

---

## Agent Definitions

### Agent YAML Structure

All agents follow this structure in `src/agents/definitions/`:

```yaml
kind: Agent
name: AgentName
description: |
  Brief description of the agent's purpose.

instructions: |
  Detailed instructions for the agent's behavior.
  Include: responsibilities, guidelines, escalation rules.

model:
  id: =Env.MODEL_DEPLOYMENT_SIMPLE    # or _STANDARD, _COMPLEX
  provider: AzureAIAgentClient
  connection:
    kind: remote
    endpoint: =Env.AZURE_AI_PROJECT_ENDPOINT
  options:
    temperature: 0.3
    maxOutputTokens: 2000

# Structured output (optional, used in Controlled mode)
outputSchema:
  properties:
    PropertyName:
      type: boolean|string|number
      required: true|false
      description: |
        Description of what this property represents.

# Tools (optional)
tools:
  - kind: file_search
    vectorStoreIds:
      - vs_xxx
  - kind: mcp
    name: tool_name
    url: =Env.MCP_URL
```

### Current Agents

| Agent | File | Purpose |
|-------|------|---------|
| Orchestrator (Native) | `orchestrator_native.yaml` | Routes via tool calls |
| Orchestrator (Controlled) | `orchestrator_controlled.yaml` | Routes via JSON Intent |
| Support | `support.yaml` | First-level support with RAG |
| Ticketing | `ticketing.yaml` | Creates support tickets |

---

## Workflow Variants

The platform implements **two workflow variants** for comparison:

### Native Variant

**File:** `src/workflows/handoff_native.py`

In Native mode:
- Orchestrator uses auto-generated `handoff_to_support()`, `handoff_to_ticketing()` tools
- The LLM decides which tool to call based on instructions
- Routing is fully decentralized

**Pros:**
- Simple, natural LLM behavior
- Framework handles routing logic
- Minimal custom code

**Cons:**
- Less control over routing decisions
- LLM might make incorrect choices

### Controlled Variant

**File:** `src/workflows/handoff_controlled.py`

In Controlled mode:
- Orchestrator returns JSON with `Intent` field
- Python code reads Intent and forces handoff
- Full control over routing in Python

**Pros:**
- Predictable, deterministic routing
- Easy to debug and log
- Custom business logic

**Cons:**
- More code to maintain
- Requires JSON parsing

### Comparison

| Aspect | Native | Controlled |
|--------|--------|------------|
| Routing decision | LLM via tool calls | Python via Intent |
| Control | Low | High |
| Debugging | Hard | Easy |
| Logging | Limited | Full |
| Code complexity | Low | Medium |

---

## Adding New Agents

### Step 1: Create Agent YAML

Create a new file in `src/agents/definitions/`:

```yaml
# src/agents/definitions/billing.yaml
kind: Agent
name: Billing
description: |
  Handles billing inquiries and payment issues.

instructions: |
  You are the Billing agent for DistriPartner.
  
  ## Your Responsibilities
  - Answer billing questions
  - Help with payment issues
  - Check subscription status
  
  ## When to Escalate
  - Refund requests go to Ticketing
  - Technical issues go to Support

model:
  id: =Env.MODEL_DEPLOYMENT_SIMPLE
  provider: AzureAIAgentClient
  connection:
    kind: remote
    endpoint: =Env.AZURE_AI_PROJECT_ENDPOINT
```

### Step 2: Add Loading Function

In `src/workflows/agents.py`:

```python
async def load_billing_agent(credential: DefaultAzureCredential) -> ChatAgent:
    """Load the Billing agent."""
    return await load_agent_from_yaml("billing.yaml", credential)
```

### Step 3: Register in HandoffBuilder

In `src/workflows/handoff_native.py`:

```python
async def build_native_workflow(credential: DefaultAzureCredential) -> Workflow:
    # Load agents
    orchestrator = await load_orchestrator_native(credential)
    support = await load_support_agent(credential)
    ticketing = await load_ticketing_agent(credential)
    billing = await load_billing_agent(credential)  # NEW
    
    # Build workflow
    workflow = (
        HandoffBuilder(
            name="distripartner_native",
            participants=[orchestrator, support, ticketing, billing],  # ADD
        )
        .with_start_agent(orchestrator)
        .add_handoff(orchestrator, [support, ticketing, billing])  # ADD
        .add_handoff(billing, [ticketing, support])  # Define billing paths
        .add_handoff(support, [ticketing])
        .build()
    )
    return workflow
```

### Step 4: Update Orchestrator Instructions

In `orchestrator_native.yaml`, add:

```yaml
instructions: |
  ...
  ### handoff_to_billing
  Use this tool when the user:
  - Has billing or payment questions
  - Asks about invoices or charges
  - Wants to check subscription status
```

### Step 5: Register for Individual Testing

In `src/run_agent.py`:

```python
AVAILABLE_AGENTS = {
    ...
    "billing": "billing.yaml",
}
```

### Step 6: Test

```bash
# Test individually
python run_agent.py --agent billing

# Test in workflow
python run_workflow.py --mode native
```

---

## Human-in-the-Loop Pattern

The workflow supports multi-turn conversations with user input.

### How It Works

1. Workflow calls `workflow.run(user_message)`
2. Agent responds, workflow emits `RequestInfoEvent`
3. Workflow pauses, returns control to Python
4. Python collects user input
5. Workflow continues with `workflow.send_responses(responses)`

### Code Pattern

```python
# Start workflow
events = await workflow.run(user_message)
pending_requests = extract_requests(events)

# Conversation loop
while pending_requests:
    user_input = get_user_input()
    
    responses = {
        req.request_id: HandoffAgentUserRequest.create_response(user_input)
        for req in pending_requests
    }
    
    events = await workflow.send_responses(responses)
    pending_requests = extract_requests(events)
```

### Event Types

| Event | Purpose |
|-------|---------|
| `AgentRunEvent` | Agent completed response |
| `AgentRunUpdateEvent` | Streaming update |
| `HandoffSentEvent` | Handoff initiated |
| `RequestInfoEvent` | Waiting for user input |
| `WorkflowOutputEvent` | Workflow completed |
| `WorkflowStatusEvent` | State change (IDLE, etc.) |

---

## Folder Structure

```
DistriPartnerSimplePlatform/
├── docs/
│   ├── ARCHITECTURE.md          # This file
│   └── DeclarativeAgents.md     # YAML schema reference
├── src/
│   ├── run_agent.py             # Run individual agents
│   ├── run_workflow.py          # Run multi-agent workflow
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── agents.py            # Agent loading
│   │   ├── common.py            # Shared utilities
│   │   ├── handoff_native.py    # Native variant
│   │   └── handoff_controlled.py # Controlled variant
│   └── agents/
│       └── definitions/          # Agent YAML files
│           ├── orchestrator_native.yaml
│           ├── orchestrator_controlled.yaml
│           ├── support.yaml
│           └── ticketing.yaml
├── tests/
│   └── test_agent_schema.py     # Schema validation
├── .env.example
├── requirements.txt
└── README.md
```

---

## Troubleshooting

### Common Issues

#### "Import could not be resolved" Errors

These are Pylance analyzer errors that appear when the workspace structure is new. They don't affect runtime.

**Solution:** Restart the Python language server or reload VS Code.

#### Agent Loading Fails

**Error:** `Agent definition not found: /path/to/agent.yaml`

**Solution:** 
1. Check the YAML file exists in `src/agents/definitions/`
2. Verify the filename matches what's in `agents.py`
3. Ensure the YAML is valid syntax

#### Handoff Tools Not Working

**Error:** Agent doesn't call handoff tools

**Solution:**
1. Check the agent's instructions mention the handoff tools
2. Verify `add_handoff()` is configured correctly
3. Test the agent individually with `run_agent.py`

#### PowerFx Expression Errors

**Error:** Errors with `=Env.VARIABLE_NAME`

**Solution:**
1. Ensure the variable is set in `.env`
2. Verify `safe_mode=False` in `AgentFactory`
3. Check the `.env` file path is correct

### Debug Mode

Run workflow with verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [HandoffBuilder Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/workflows/orchestration)
- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
