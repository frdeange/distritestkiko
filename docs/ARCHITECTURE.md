# DistriPartner Platform - Architecture Reference

This document describes the architecture of the DistriPartner Platform, a multi-agent system built with Microsoft Agent Framework using the **HandoffBuilder** pattern and **AzureOpenAIResponsesClient** for LLM-driven agent orchestration.

## Table of Contents

- [Overview](#overview)
- [Architecture: HandoffBuilder](#architecture-handoffbuilder)
- [Handoff Topology](#handoff-topology)
- [Agent Definitions](#agent-definitions)
- [Structured Output](#structured-output)
- [MCP Tool Integration](#mcp-tool-integration)
- [Backend Integration (Teams Bot)](#backend-integration-teams-bot)
- [Adding New Agents](#adding-new-agents)
- [Folder Structure](#folder-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

DistriPartner Platform is a customer support system that uses multiple specialized AI agents to handle user requests. The system uses:

- **AzureOpenAIResponsesClient** for creating agents (Azure AI Foundry project endpoint)
- **HandoffBuilder** for wiring directed handoffs between agents
- **LLM-driven routing**: Agents decide when to hand off by calling `handoff_to_<AgentName>` tools
- **Pydantic models** for structured output (`response_format`)
- **MCP (Model Context Protocol)** for external tool integration (CosmosDB, EntraID, Email, Microsoft Learn)

### Key Principles

1. **LLM-Driven Routing**: The LLM decides when to hand off to another agent via tool calls — no PowerFx or condition groups
2. **Structured Output**: All agents return Pydantic-validated JSON
3. **Separation of Concerns**: Each agent has a specific responsibility with its own instruction YAML + tools
4. **Human-in-the-Loop**: Multi-turn conversations via `HandoffAgentUserRequest` events
5. **Cost Optimization**: Four model tiers (complex, standard, simple, mini) assigned per agent
6. **Least-Privilege Tools**: Each agent receives only the MCP tools it needs via `allowed_tools` filtering
7. **Autonomous Agents**: DataGatherer and Communication run without user interaction

---

## Architecture: HandoffBuilder

The platform uses the **HandoffBuilder** pattern from `agent_framework.orchestrations`.

### How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HANDOFF BUILDER WORKFLOW                        │
├─────────────────────────────────────────────────────────────────────┤
│  orchestration/handoff.py  → Agent creation + HandoffBuilder wiring │
│  agents/instructions/*.yaml → Agent instructions (English-only)    │
│  agents/response_models.py → Pydantic structured output models     │
├─────────────────────────────────────────────────────────────────────┤
│                     BACKEND (Teams Bot)                             │
├─────────────────────────────────────────────────────────────────────┤
│  backend/workflow_manager.py → Session management, event streaming  │
│  backend/bot.py              → Teams channel adapter (M365 SDK)     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `AzureOpenAIResponsesClient` | Creates agents using Azure AI Foundry project endpoint |
| `HandoffBuilder` | Wires directed handoffs between agents, builds the `Workflow` |
| `handoff_to_<Agent>` tools | Auto-generated tools the LLM calls to route to another agent |
| `HandoffAgentUserRequest` | Event emitted when an agent needs user input |
| `with_autonomous_mode()` | Marks agents that run without user interaction |
| `response_format` | Pydantic model enabling structured JSON output |

---

## Handoff Topology

```
                    ┌─────────────────┐
           ┌──────▶│   Orchestrator   │◀──────┐
           │       │  (Intent Class.) │       │
           │       │  gpt-4.1-mini   │       │
           │       └────────┬────────┘       │
           │                │                 │
           │   ┌────────────┴────────────┐   │
           │   │                         │   │
           │   ▼                         ▼   │
      ┌────────────────┐        ┌───────────────┐
      │    Support      │       │   Ticketing    │
      │  (L1 Troublesh.)│──────▶│ (Create ticket)│
      │  gpt-4.1        │       │  gpt-4.1       │
      └────────┬───────┘       └───────┬────────┘
               │                       │  │
               │               ┌───────┘  │
               │               ▼          ▼
               │    ┌──────────────┐  ┌──────────────┐
               │    │ DataGatherer │  │Communication │
               │    │(EntraID+Cosmos│  │(Email notify)│
               │    │ gpt-4.1-mini │  │ gpt-4.1-mini │
               │    │  AUTONOMOUS  │  │  AUTONOMOUS  │
               │    └──────┬───────┘  └──────────────┘
               │           │
               │           ▼
               │        (back to Ticketing)
               │
               └──────▶ (back to Orchestrator)
```

### Directed Handoffs

| Source | Targets | When |
|--------|---------|------|
| Orchestrator | Support, Ticketing | After classifying intent |
| Support | Ticketing, Orchestrator | Escalation or resolution |
| Ticketing | DataGatherer, Communication, Orchestrator | Data enrichment, email, or completion |
| DataGatherer | Ticketing | Return gathered profile data (autonomous) |
| Communication | Orchestrator | After sending email (autonomous) |

### How Routing Works

1. The LLM receives the user message and the agent's instructions
2. Instructions describe when to use each `handoff_to_<Agent>` tool
3. The LLM calls the handoff tool → HandoffBuilder routes to the target agent
4. The target agent receives the full conversation history
5. Autonomous agents (DataGatherer, Communication) complete without user input

---

## Agent Definitions

All agent instructions are in `src/agents/instructions/` as YAML files. All prompts are in **English**, with a language-matching rule:

> *"Always respond in the same language the user writes in."*

### Current Agents

| Agent | File | Model Tier | Tools | Mode |
|-------|------|-----------|-------|------|
| Orchestrator | `orchestrator.yaml` | **Mini** (gpt-4.1-mini) | None | Interactive |
| Support | `support.yaml` | Simple (gpt-4.1) | Microsoft Learn MCP | Interactive |
| Ticketing | `ticketing.yaml` | Simple (gpt-4.1) | CosmosDB MCP | Interactive |
| DataGatherer | `datagatherer.yaml` | **Mini** (gpt-4.1-mini) | EntraID + CosmosDB MCP | **Autonomous** |
| Communication | `communication.yaml` | **Mini** (gpt-4.1-mini) | Email MCP | **Autonomous** |

### Instruction YAML Structure

```yaml
instructions: |
  You are the [Agent Name] agent for DistriPartner, a Microsoft CSP partner.

  ## Language Rule
  Always respond in the same language the user writes in.

  ## Your Role
  Description of the agent's responsibilities.

  ## Handoff Tools
  ### handoff_to_TargetAgent
  When to use this handoff tool.
```

---

## Structured Output

### Pydantic Response Models

Each agent has a corresponding Pydantic model in `src/agents/response_models.py`, passed as `response_format` when creating agents.

| Agent | Model | Key Fields |
|-------|-------|------------|
| Orchestrator | `OrchestratorResponse` | `Intent`, `IntentClassified`, `Summary`, `Response` |
| Support | `SupportResponse` | `IsResolved`, `NeedsTicket`, `ResolutionSummary`, `Category`, `Response` |
| DataGatherer | `DataGathererResponse` | `userId`, `email`, `displayName`, `organization`, `subscriptionId`, `tenantId` |
| Ticketing | `TicketingResponse` | `TicketCreated`, `TicketId`, `Status`, `ProductFamily`, `Priority`, `Response` |
| Communication | `CommunicationResponse` | `emailSent`, `error`, `recipientCount`, `Response` |

All interactive agents include a `Response` field — the natural-language message shown to the user. The `WorkflowManager` extracts this field from the JSON output.

---

## MCP Tool Integration

Agents connect to external services via MCP (Model Context Protocol) servers.

| MCP Server | Env Variable | Used By | `allowed_tools` |
|------------|-------------|---------|-----------------|
| Microsoft Learn | `MCP_LEARN_URL` | Support | (all — public, no filtering) |
| CosmosDB | `MCP_COSMOSDB_URL` | DataGatherer, Ticketing | DataGatherer: `resourcegraph_query`, `cosmos_item_query`; Ticketing: + `cosmos_item_upsert`, `cosmos_item_get` |
| Entra ID | `MCP_ENTRAID_URL` | DataGatherer | `entraid_user_get`, `entraid_user_manager` |
| Email (ACS) | `MCP_EMAIL_URL` | Communication | `communication_email_send`, `communication_email_status` |

> **Note:** CosmosDB, EntraID, and Email URLs all point to the **same Azure MCP server** (~96 tools). The `allowed_tools` parameter filters each agent to only the tools it needs.

MCP tools are configured via `AzureOpenAIResponsesClient.get_mcp_tool()` with `approval_mode="never_require"` for autonomous execution.

---

## Backend Integration (Teams Bot)

### WorkflowManager

`src/backend/workflow_manager.py` manages per-conversation workflow sessions:

1. **Session creation**: Calls `create_handoff_workflow(credential, user_identity)` once per conversation
2. **Message processing**: Sends user input into the workflow via `workflow.run()`
3. **Event streaming**: Iterates `async for event in workflow.run(...)`:
   - `HandoffAgentUserRequest`: Agent needs user input → extract response text → stream to Teams
   - Other events: Agent handoffs, tool calls (logged)
4. **Resume**: On next user message, creates `HandoffAgentUserRequest.create_response(user_input)` and passes to `workflow.run(responses=...)`
5. **Response extraction**: Parses the `Response` field from JSON structured output via `_extract_response_text()`

### Bot

`src/backend/bot.py` is the Teams channel adapter using M365 Agents SDK (`AgentApplication`). It:
- Handles `/reset` command to clear conversation state
- Delegates message processing to `WorkflowManager`
- Streams responses via `context.streaming_response.queue_text_chunk()`
- Stores state in CosmosDB via `workflow_state.py`

---

## Adding New Agents

### Step 1: Create Instruction YAML

Create `src/agents/instructions/newagent.yaml`:

```yaml
instructions: |
  You are the NewAgent for DistriPartner, a Microsoft CSP partner.

  ## Language Rule
  Always respond in the same language the user writes in.

  ## Your Role
  Handle [specific responsibility].

  ## Handoff Tools
  ### handoff_to_Orchestrator
  Use when the task is complete or the user needs a different type of help.
```

### Step 2: Create Pydantic Response Model

In `src/agents/response_models.py`:

```python
class NewAgentResponse(BaseModel):
    completed: bool = Field(description="Whether the task was completed.")
    Response: str = Field(default="", description="Message shown to user.")
```

### Step 3: Register in handoff.py

In `src/orchestration/handoff.py`:

```python
from agents.response_models import NewAgentResponse

newagent = simple_client.as_agent(
    name="NewAgent",
    instructions=_read_instructions("newagent.yaml"),
    default_options={"response_format": NewAgentResponse},
)

# Add to participants list
builder = HandoffBuilder(
    name="DistriPartnerWorkflow",
    participants=[orchestrator, support, ticketing, datagatherer, communication, newagent],
    ...
)

# Add handoff routes
builder.add_handoff(source=orchestrator, targets=[support, ticketing, newagent], ...)
builder.add_handoff(source=newagent, targets=[orchestrator], ...)
```

### Step 4: Update Orchestrator Instructions

In `src/agents/instructions/orchestrator.yaml`, add:

```yaml
### handoff_to_NewAgent
Use this tool when the user needs [describe when to route here].
```

---

## Folder Structure

```
DistriPartnerSimplePlatform/
├── docs/
│   ├── ARCHITECTURE.md            # This file
│   └── support-kb/                # Knowledge base articles
│       ├── 01-azure-foundry-basics.md
│       ├── 02-microsoft-365-copilot.md
│       ├── 03-azure-communication-services.md
│       ├── 04-faq-distripartner.md
│       └── 05-troubleshooting-azure-errors.md
├── scripts/
│   ├── setup_ai_search.py         # Azure AI Search provisioning
│   └── setup_cosmos.py            # CosmosDB provisioning
├── src/
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── handoff.py             # HandoffBuilder workflow factory
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── response_models.py     # Pydantic structured output models
│   │   └── instructions/          # Agent instruction YAML files
│   │       ├── orchestrator.yaml
│   │       ├── support.yaml
│   │       ├── ticketing.yaml
│   │       ├── datagatherer.yaml
│   │       └── communication.yaml
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── bot.py                 # Teams bot (M365 Agents SDK)
│   │   ├── config.py              # Environment configuration
│   │   ├── cosmos_store.py        # CosmosDB storage helpers
│   │   ├── main.py                # Application entry point
│   │   ├── start_server.py        # AIOHTTP server startup
│   │   ├── workflow_manager.py    # Per-conversation workflow session manager
│   │   └── workflow_state.py      # CosmosDB state storage
│   └── frontend/
│       ├── DistriPartnerSupport.zip # Pre-packaged Teams app
│       └── teams-manifest/        # Teams app manifest
│           ├── manifest.json
│           ├── color.png
│           ├── outline.png
│           └── generate_icons.py
├── tests/
│   └── test_agent_schema.py       # Schema validation tests
├── Dockerfile                     # Container image for Azure Container Apps
├── requirements.txt               # Python dependencies
└── README.md
```

---

## Troubleshooting

### Common Issues

#### Agent Doesn't Route Correctly

**Symptom:** Agent doesn't call `handoff_to_<Agent>` when expected.

**Solution:**
1. Check the agent's instruction YAML has a `## Handoff Tools` section describing when to use each handoff
2. Verify the handoff is registered in `handoff.py` via `builder.add_handoff(source=..., targets=[...])`
3. Check model tier — Mini models may need clearer instructions

#### MCP Connection Issues

**Symptom:** MCP tool calls fail or timeout.

**Solution:**
1. Verify MCP URLs in `.env` are correct
2. Check the Azure MCP server is reachable from the runtime environment
3. Ensure Managed Identity has appropriate role assignments
4. For Microsoft Learn MCP, verify network access (no auth required)

#### Structured Output Parsing Errors

**Symptom:** `_extract_response_text()` returns raw JSON instead of the Response field.

**Solution:**
1. Verify the Pydantic model has a `Response` field
2. Check the agent's instructions tell it to populate the `Response` field with the user-facing message
3. Test the agent individually to see its raw output

#### Language Issues

**Symptom:** Agent responds in the wrong language.

**Solution:**
1. Ensure the `## Language Rule` section is present at the top of the agent's instruction YAML
2. Verify all prompts are in English (not bilingual)
3. Check that no hardcoded Spanish/other language text remains in instructions

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [HandoffBuilder Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/orchestrations)
- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
