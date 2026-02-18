# DistriPartner Platform - Architecture Reference

This document describes the architecture of the DistriPartner Platform, a multi-agent system built with Microsoft Agent Framework using **declarative YAML-defined workflows** and **AzureOpenAIResponsesClient** for agent orchestration.

## Table of Contents

- [Overview](#overview)
- [Architecture: Declarative Workflow](#architecture-declarative-workflow)
- [Workflow Flow](#workflow-flow)
- [Agent Definitions](#agent-definitions)
- [Structured Output & Routing](#structured-output--routing)
- [MCP Tool Integration](#mcp-tool-integration)
- [Adding New Agents](#adding-new-agents)
- [Entry Points](#entry-points)
- [Folder Structure](#folder-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

DistriPartner Platform is a customer support system that uses multiple specialized AI agents to handle user requests. The system uses:

- **AzureOpenAIResponsesClient** for creating agents (recommended by Microsoft for orchestrations)
- **WorkflowFactory** for loading declarative YAML workflow definitions
- **Pydantic models** for structured output (`response_format`) enabling PowerFx condition evaluation
- **MCP (Model Context Protocol)** for external tool integration (CosmosDB, EntraID, Email, Microsoft Learn)

### Key Principles

1. **Declarative Routing**: Workflow orchestration defined in YAML with ConditionGroup and PowerFx expressions
2. **Structured Output**: All workflow agents return Pydantic-validated JSON for deterministic routing
3. **Separation of Concerns**: Each agent has a specific responsibility (YAML instructions + tools)
4. **Human-in-the-Loop**: Multi-turn conversations via `externalLoop` in the workflow YAML
5. **Cost Optimization**: Four model tiers (complex, standard, simple, mini) assigned per agent
6. **Least-Privilege Tools**: Each agent receives only the MCP tools it needs via `allowed_tools` filtering

---

## Architecture: Declarative Workflow

The platform uses the **Declarative Workflow** pattern based on guidance from the Microsoft Agent Framework team ([Issue #3713](https://github.com/microsoft/agent-framework/issues/3713)).

### How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DECLARATIVE (YAML)                              │
├─────────────────────────────────────────────────────────────────────┤
│  workflow.yaml         → Routing, conditions, loops, agent order    │
│  Agent YAML files      → Instructions, tools, output schemas        │
├─────────────────────────────────────────────────────────────────────┤
│                     PYTHON GLUE                                     │
├─────────────────────────────────────────────────────────────────────┤
│  declarative.py        → Agent creation, MCP setup, workflow I/O    │
│  response_models.py    → Pydantic models for structured output      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `AzureOpenAIResponsesClient` | Creates agents using Azure AI Foundry project endpoint |
| `WorkflowFactory` | Loads workflow definition from YAML |
| `InvokeAzureAgent` | YAML action that invokes an agent by name |
| `ConditionGroup` | YAML action for PowerFx-based routing |
| `externalLoop` | YAML input config for multi-turn user conversations |
| `response_format` | Pydantic model enabling structured JSON output |

---

## Workflow Flow

### Support & Ticketing Flow

```
                    ┌─────────────────┐
                    │   Orchestrator   │ ◄── externalLoop (chitchat)
                    │  (Intent Class.) │     Model: gpt-4.1-mini
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │ intent=support              │ intent=ticketing
              ▼                              │
     ┌────────────────┐                      │
     │    Support      │ ◄── externalLoop    │
     │  (L1 Troublesh.)│   (not resolved     │
     └───────┬────────┘    & not needs_ticket)│
             │                               │
     ┌───────┴───────┐                       │
     │ IsResolved?   │                       │
     │  ├─ YES → END │                       │
     │  └─ NO  ──────┼───────────────────────┘
     │               │
     └───────────────┘
              │
     ┌────────┴────────┐
     │  DataGatherer    │  Model: gpt-4.1-mini
     │ (EntraID + Cosmos│  Tools: entraid_user_get,
     │  in one step)    │  cosmos_item_query, etc.
     └────────┬────────┘
              │
     ┌────────┴────────┐
     │    Ticketing     │ ◄── externalLoop (ticket not created)
     │ (Create ticket)  │     Tools: cosmos_item_upsert, etc.
     └────────┬────────┘
              │
     ┌────────┴────────┐
     │  Communication   │  Model: gpt-4.1-mini
     │  (Email notify)  │  Tools: communication_email_send
     └─────────────────┘
```

### Routing Logic

| Step | From | To | Condition (PowerFx) |
|------|------|----|---------------------|
| 1 | User | Orchestrator | `OnConversationStart` |
| 1a | Orchestrator | Orchestrator (loop) | `Intent = "chitchat" Or Not(IntentClassified)` |
| 2a | Orchestrator | Support | `Intent = "support"` |
| 2b | Orchestrator | Ticketing Steps | `Intent = "ticketing"` |
| 3 | Support | Support (loop) | `Not(IsResolved) And Not(NeedsTicket)` |
| 3a | Support | END | `IsResolved = true` |
| 3b | Support | DataGatherer | `NeedsTicket = true` |
| 4 | DataGatherer | Ticketing | Always (sequential) |
| 5 | Ticketing | Ticketing (loop) | `Not(TicketCreated)` |
| 6 | Ticketing | Communication | `TicketCreated = true` |

---

## Agent Definitions

All agents are defined in `src/agents/definitions/` as YAML files.

### Current Agents

| Agent | File | Model Tier | Tools (`allowed_tools`) | Purpose |
|-------|------|-----------|------------------------|--------|
| Orchestrator | `orchestrator_controlled.yaml` | **Mini** | None | Classifies user intent into support/ticketing/chitchat |
| Support | `support.yaml` | Simple | Microsoft Learn MCP (separate server, no filtering) | First-level troubleshooting with RAG |
| DataGatherer | `dataGatherer.yaml` | **Mini** | EntraID: `entraid_user_get`, `entraid_user_manager`; CosmosDB: `resourcegraph_query`, `cosmos_item_query` | Retrieves user profile + subscription data in one step |
| Ticketing | `ticketing.yaml` | Simple | CosmosDB: `resourcegraph_query`, `cosmos_item_upsert`, `cosmos_item_query`, `cosmos_item_get` | Creates support tickets, stores in CosmosDB |
| Communication | `communication.yaml` | **Mini** | Email: `communication_email_send`, `communication_email_status` | Sends email notifications to support team |

### Agent YAML Structure

```yaml
kind: Prompt
name: AgentName
description: |
  Brief description of the agent's purpose.

instructions: |
  Detailed instructions for the agent's behavior.

model:
  id: =Env.MODEL_DEPLOYMENT_SIMPLE    # or _STANDARD, _COMPLEX, _MINI
  connection:
    kind: remote
    endpoint: =Env.AZURE_AI_PROJECT_ENDPOINT
  options:
    temperature: 0.3
    maxOutputTokens: 2000

outputSchema:
  properties:
    PropertyName:
      type: boolean|string|number
      required: true|false
      description: |
        Description of what this property represents.

tools:
  - kind: mcp
    name: tool_name
    url: =Env.MCP_URL
    connection:
      kind: remote
      name: =Env.MCP_CONNECTION_NAME
    approvalMode:
      kind: never
```

---

## Structured Output & Routing

### Pydantic Response Models

Each workflow agent has a corresponding Pydantic model in `src/workflows/response_models.py` that defines its structured output. These models are passed as `response_format` when creating agents via `AzureOpenAIResponsesClient.as_agent()`.

| Agent | Model | Key Fields |
|-------|-------|------------|
| Orchestrator | `OrchestratorResponse` | `Intent`, `IntentClassified`, `Summary` |
| Support | `SupportResponse` | `IsResolved`, `NeedsTicket`, `ResolutionSummary`, `Category` |
| DataGatherer | `DataGathererResponse` | `userId`, `email`, `displayName`, `organization`, `subscriptionId`, `tenantId`, `domain` |
| Ticketing | `TicketingResponse` | `TicketCreated`, `TicketId`, `Status`, `ProductFamily`, `Priority` |
| Communication | `CommunicationResponse` | `emailSent`, `error`, `recipientCount` |

### How Routing Works

1. Agent returns structured JSON matching its Pydantic model
2. Workflow YAML stores the output in a local variable (e.g., `Local.SupportOutput`)
3. `ConditionGroup` evaluates PowerFx expressions against the output
4. `externalLoop.when` controls multi-turn conversation loops

```yaml
# Example: Route based on Orchestrator output
- kind: ConditionGroup
  conditions:
    - condition: =Local.OrchestratorOutput.Intent = "support"
      actions: [...]
    - condition: =Local.OrchestratorOutput.Intent = "ticketing"
      actions: [...]

# Example: Loop until resolved
- kind: InvokeAzureAgent
  agent:
    name: Support
  input:
    externalLoop:
      when: =Not(Local.SupportOutput.IsResolved) And Not(Local.SupportOutput.NeedsTicket)
```

---

## MCP Tool Integration

Agents connect to external services via MCP (Model Context Protocol) servers.

| MCP Server | Env Variable | Used By | `allowed_tools` | Purpose |
|------------|-------------|---------|-----------------|--------|
| CosmosDB | `MCP_COSMOSDB_URL` | DataGatherer, Ticketing | DataGatherer: `resourcegraph_query`, `cosmos_item_query`; Ticketing: `resourcegraph_query`, `cosmos_item_upsert`, `cosmos_item_query`, `cosmos_item_get` | Query/store subscription and ticket data |
| Entra ID | `MCP_ENTRAID_URL` | DataGatherer | `entraid_user_get`, `entraid_user_manager` | Query user identity and profile data |
| Email (ACS) | `MCP_EMAIL_URL` | Communication | `communication_email_send`, `communication_email_status` | Send email notifications |
| Microsoft Learn | `MCP_LEARN_URL` | Support | (all — separate server) | Public documentation search (no auth) |

> **Note:** `MCP_COSMOSDB_URL`, `MCP_ENTRAID_URL`, and `MCP_EMAIL_URL` all point to the **same Azure MCP server** (~96 tools). The `allowed_tools` parameter in `declarative.py` filters each agent to only the tools it needs (2–4 tools per agent instead of 96).

MCP tools are authenticated via Azure AI Foundry project connections using the `MCP_CONNECTION_NAME` variable (Managed Identity-based).

---

## Adding New Agents

### Step 1: Create Agent YAML

Create a new file in `src/agents/definitions/`:

```yaml
kind: Prompt
name: Billing
description: |
  Handles billing inquiries and payment issues.
instructions: |
  You are the Billing agent for DistriPartner.
  ## Your Responsibilities
  - Answer billing questions
  - Help with payment issues
model:
  id: =Env.MODEL_DEPLOYMENT_SIMPLE
  connection:
    kind: remote
    endpoint: =Env.AZURE_AI_PROJECT_ENDPOINT
  options:
    temperature: 0.3
    maxOutputTokens: 2000
```

### Step 2: Create Pydantic Response Model

In `src/workflows/response_models.py`:

```python
class BillingResponse(BaseModel):
    resolved: bool = Field(description="Whether the billing issue was resolved.")
    summary: str = Field(default="", description="Summary of the billing interaction.")
```

### Step 3: Register in declarative.py

In `src/workflows/declarative.py`, add:

```python
# If the agent needs MCP tools, create per-agent instances with allowed_tools:
billing_cosmos_tools = get_mcp_tool(
    url=os.getenv("MCP_COSMOSDB_URL"),
    connection_id=mcp_conn_id,
    allowed_tools=["cosmos_item_query", "cosmos_item_get"],
)

billing = simple_client.as_agent(
    name="Billing",
    instructions=_read_instructions("billing.yaml"),
    default_options={"response_format": BillingResponse},
    tools=[billing_cosmos_tools],
)
```

And add `"Billing": billing` to the agents registry dict.

### Step 4: Add to Workflow YAML

In `src/workflows/workflow.yaml`, add an `InvokeAzureAgent` action and routing conditions.

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
python src/run_agent.py --agent billing

# Test in workflow
python src/run_workflow.py
```

---

## Entry Points

| Script | Purpose | Usage |
|--------|---------|-------|
| `src/run_workflow.py` | Run multi-agent declarative workflow | `python src/run_workflow.py [--streaming]` |
| `src/run_agent.py` | Run individual agents for testing | `python src/run_agent.py --agent support` |

---

## Folder Structure

```
DistriPartnerSimplePlatform/
├── docs/
│   ├── ARCHITECTURE.md            # This file
│   └── DeclarativeAgents.md       # YAML schema reference
├── src/
│   ├── run_agent.py               # Run individual agents (AgentFactory)
│   ├── run_workflow.py            # Run declarative workflow
│   ├── workflows/
│   │   ├── __init__.py            # Module exports
│   │   ├── declarative.py         # Agent creation + workflow runner
│   │   ├── response_models.py     # Pydantic structured output models
│   │   └── workflow.yaml          # Declarative workflow definition
│   └── agents/
│       └── definitions/           # Agent YAML files
│           ├── orchestrator_controlled.yaml
│           ├── support.yaml
│           ├── dataGatherer.yaml   # Fused Profiler + DataCollector
│           ├── ticketing.yaml
│           └── communication.yaml
├── tests/
│   └── test_agent_schema.py       # Schema validation tests
├── .env.example                   # Environment template
├── requirements.txt
└── README.md
```

---

## Troubleshooting

### Common Issues

#### PowerFx Expression Errors

**Error:** Errors with `=Env.VARIABLE_NAME` or `=Local.OutputName.Property`

**Solution:**
1. Ensure the variable is set in `.env`
2. Verify `safe_mode=False` in `AgentFactory` (for `run_agent.py`)
3. For workflow variables, check that the agent's Pydantic model has the referenced field

#### Agent Loading Fails

**Error:** `Agent definition not found: /path/to/agent.yaml`

**Solution:**
1. Check the YAML file exists in `src/agents/definitions/`
2. Verify the filename in `declarative.py` matches
3. Ensure the YAML is valid syntax

#### MCP Connection Issues

**Error:** MCP tool calls fail or timeout

**Solution:**
1. Verify MCP URLs in `.env` are correct
2. Check the `MCP_CONNECTION_NAME` matches your Azure AI Foundry connection
3. Ensure the Managed Identity has appropriate role assignments
4. For Microsoft Learn MCP, verify network access (no auth required)

#### Structured Output Parsing Errors

**Error:** Workflow cannot route because agent output doesn't match expected schema

**Solution:**
1. Verify the agent's YAML `outputSchema` matches the Pydantic model in `response_models.py`
2. Check the PowerFx expression references in `workflow.yaml` match the Pydantic field names
3. Test the agent individually with `run_agent.py` to see its raw output

### Debug Mode

Run workflow with verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Declarative Workflow Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/workflows/customer_support)
- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
