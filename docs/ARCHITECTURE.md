# DistriPartner Platform - Architecture Reference

This document describes the architecture of the DistriPartner Platform, a multi-agent system built with Microsoft Agent Framework using declarative YAML definitions.

## Table of Contents

- [Overview](#overview)
- [Workflow Architecture](#workflow-architecture)
- [Agent Definitions](#agent-definitions)
- [Declarative Workflow Pattern](#declarative-workflow-pattern)
- [MCP Integration](#mcp-integration)
- [Adding New Agents](#adding-new-agents)
- [Adding New Workflows](#adding-new-workflows)
- [Folder Structure](#folder-structure)
- [Future: Teams Integration](#future-teams-integration)

---

## Overview

DistriPartner Platform is a customer support and campaign management system that uses multiple specialized AI agents to handle user requests. The system uses:

- **Declarative YAML** for agent and workflow definitions
- **Microsoft Agent Framework** for orchestration
- **Azure AI Foundry** for LLM capabilities
- **MCP (Model Context Protocol)** for external tool integration

### Key Principles

1. **Declarative First**: Agents and workflows are defined in YAML, not code
2. **Separation of Concerns**: Each agent has a specific responsibility
3. **Structured Output**: Agents return structured data for routing decisions
4. **Human-in-the-Loop**: Workflows support multi-turn conversations with users

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
| Orchestrator | Support | `Intent = "support"` - Questions, troubleshooting, documentation |
| Orchestrator | Ticketing | `Intent = "ticketing"` - Explicit ticket requests |
| Support | Ticketing | `NeedsTicket = true` - Cannot resolve, needs escalation |
| Support | End | `IsResolved = true` - Issue resolved |
| Ticketing | End | `TicketCreated = true` - Ticket created successfully |

### Future: Campaign Flow (Backlog)

```
     Orchestrator
          │
          ▼
   CampaignManager ──► Profiler ──► DataCollector ──► Communication
```

---

## Agent Definitions

### Agent YAML Structure

All agents follow this structure:

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

# CRITICAL: Structured output for workflow routing
outputSchema:
  properties:
    PropertyName:
      type: boolean|string|number
      required: true|false
      description: |
        Description of what this property represents.

# Optional: External tools via MCP
tools:
  - kind: mcp
    name: tool_name
    description: |
      What this tool does.
    url: =Env.MCP_URL
    connection:
      kind: remote
      name: =Env.MCP_CONNECTION_NAME
    approvalMode:
      kind: never
```

### Required outputSchema Properties

#### Orchestrator
```yaml
outputSchema:
  properties:
    IntentClassified:
      type: boolean      # Has intent been determined?
    Intent:
      type: string       # "support" | "ticketing"
    Summary:
      type: string       # Summary for next agent
```

#### Support
```yaml
outputSchema:
  properties:
    IsResolved:
      type: boolean      # Issue resolved?
    NeedsTicket:
      type: boolean      # Needs escalation to Ticketing?
    ResolutionSummary:
      type: string       # What was tried/outcome
```

#### Ticketing
```yaml
outputSchema:
  properties:
    TicketCreated:
      type: boolean      # Ticket created successfully?
    TicketId:
      type: string       # Generated ticket ID
    Status:
      type: string       # "gathering_info" | "creating_ticket" | "completed" | "failed"
```

---

## Declarative Workflow Pattern

### Workflow YAML Structure

```yaml
kind: Workflow
name: WorkflowName
description: |
  Description of the workflow.

trigger:
  kind: OnConversationStart
  id: main_trigger
  actions:
    # Actions are executed sequentially
    - kind: InvokeAzureAgent
      id: unique_action_id
      agent:
        name: AgentName
      input:
        externalLoop:
          when: =Not(Local.Result.Condition)
          maxIterations: 20
      output:
        autoSend: true
        responseObject: Local.Result

    - kind: ConditionGroup
      id: routing_decision
      conditions:
        - condition: =Local.Result.Intent = "value"
          id: condition_id
          actions:
            - kind: GotoAction
              actionId: target_action_id

    - kind: EndWorkflow
      id: workflow_end
```

### Key Action Types

| Action Kind | Purpose | Usage |
|-------------|---------|-------|
| `InvokeAzureAgent` | Call an agent | Main interaction with agents |
| `ConditionGroup` | Conditional routing | Branch based on agent output |
| `GotoAction` | Jump to action | Navigate to specific action by ID |
| `SetVariable` | Set variable | Store data for later use |
| `SendActivity` | Send message | Display message to user |
| `CreateConversation` | New conversation | Isolate agent conversation |
| `EndWorkflow` | End workflow | Terminate the workflow |

### externalLoop Pattern

The `externalLoop` enables multi-turn conversations with the user:

```yaml
- kind: InvokeAzureAgent
  agent:
    name: Support
  input:
    externalLoop:
      when: |-
        =Not(Local.SupportResult.IsResolved)
          And 
          Not(Local.SupportResult.NeedsTicket)
      maxIterations: 20
  output:
    autoSend: true           # Auto-send agent responses to user
    responseObject: Local.SupportResult
```

The agent will keep conversing with the user until:
- `IsResolved = true`, OR
- `NeedsTicket = true`, OR
- `maxIterations` reached

---

## MCP Integration

### Current MCP Configuration

The platform uses a unified MCP server for all Azure services:

| Service | Tools Available | Used By |
|---------|-----------------|---------|
| **EntraID** | `entraid_user_*`, `entraid_group_*` | Profiler |
| **CosmosDB** | `cosmos_*` | DataCollector, Ticketing |
| **Communication** | `communication_email_*`, `communication_sms_*` | Ticketing, Communication |

### MCP Tool Configuration

```yaml
tools:
  - kind: mcp
    name: descriptive_name
    url: =Env.MCP_URL              # MCP server URL
    connection:
      kind: remote
      name: =Env.MCP_CONNECTION_NAME   # AI Foundry connection name
    approvalMode:
      kind: never                   # never | always | conditional
```

### Environment Variables for MCP

```bash
# MCP Server URL (unified)
MCP_COSMOSDB_URL=https://your-mcp.azurewebsites.net/mcp

# AI Foundry Connection Name
MCP_CONNECTION_NAME=AzureMCPTool
```

---

## Adding New Agents

### Step 1: Create Agent YAML

Create a new file in `src/agents/definitions/`:

```yaml
# src/agents/definitions/newagent.yaml
kind: Agent
name: NewAgent
description: |
  Description of what this agent does.

instructions: |
  Detailed instructions...

model:
  id: =Env.MODEL_DEPLOYMENT_SIMPLE
  provider: AzureAIAgentClient
  connection:
    kind: remote
    endpoint: =Env.AZURE_AI_PROJECT_ENDPOINT
  options:
    temperature: 0.3
    maxOutputTokens: 2000

# Define output for workflow routing
outputSchema:
  properties:
    ActionComplete:
      type: boolean
      required: true
      description: Whether the agent has completed its task
    # Add more properties as needed
```

### Step 2: Register in Workflow Runner

Add to `WORKFLOW_AGENTS` in `run_declarative_workflow.py`:

```python
WORKFLOW_AGENTS = {
    "Orchestrator": "orchestrator.yaml",
    "Support": "support.yaml",
    "Ticketing": "ticketing.yaml",
    "NewAgent": "newagent.yaml",  # Add new agent
}
```

### Step 3: Add to Workflow YAML

Add the agent invocation to `main-workflow.yaml`:

```yaml
- kind: InvokeAzureAgent
  id: new_agent_action
  agent:
    name: NewAgent
  input:
    externalLoop:
      when: =Not(Local.NewAgentResult.ActionComplete)
  output:
    autoSend: true
    responseObject: Local.NewAgentResult
```

### Step 4: Validate

Run the schema validation tests:

```bash
pytest tests/test_agent_schema.py
```

---

## Adding New Workflows

### Step 1: Create Workflow YAML

Create a new file in `src/agents/workflow/`:

```yaml
# src/agents/workflow/new-workflow.yaml
kind: Workflow
name: NewWorkflow
description: |
  Description of the workflow.

trigger:
  kind: OnConversationStart
  id: new_workflow_trigger
  actions:
    # Define your actions...
```

### Step 2: Create Runner Script (if needed)

Copy and modify `run_declarative_workflow.py`:

```python
WORKFLOW_FILE = WORKFLOW_DIR / "new-workflow.yaml"
WORKFLOW_AGENTS = {
    # List agents used in this workflow
}
```

---

## Folder Structure

```
DistriPartnerSimplePlatform/
├── docs/
│   └── ARCHITECTURE.md          # This file
├── src/
│   ├── agents/
│   │   ├── definitions/         # Agent YAML files
│   │   │   ├── orchestrator.yaml
│   │   │   ├── support.yaml
│   │   │   ├── ticketing.yaml
│   │   │   ├── profiler.yaml
│   │   │   ├── dataCollector.yaml
│   │   │   ├── communication.yaml
│   │   │   ├── campaignmanager.yaml
│   │   │   └── campaignSuggestor.yaml
│   │   └── workflow/            # Workflow YAML files
│   │       └── main-workflow.yaml
│   ├── backend/                 # Future: API backend
│   ├── frontend/                # Future: Web UI
│   ├── run_declarative_workflow.py   # Declarative workflow runner
│   ├── run_workflow.py          # Legacy programmatic runner
│   └── run_agent.py             # Single agent runner
├── tests/
│   └── test_agent_schema.py     # Schema validation tests
├── .env.example                 # Environment template
├── requirements.txt
└── README.md
```

---

## Future: Teams Integration

### Planned Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Microsoft Teams                       │
│                         │                               │
│                    Teams Channel                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Azure Bot Service                          │
│         (Bot Framework + Bot Adapter)                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│           Azure App Service / Functions                 │
│              (Bot Message Handler)                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│         DistriPartner Declarative Workflow             │
│    (WorkflowFactory + main-workflow.yaml)              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Azure AI Foundry (LLM)                    │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **Azure Bot Registration**: Register bot in Azure Portal
2. **Bot Adapter**: Connect Teams messages to workflow
3. **OAuth Configuration**: Enable SSO with user's Teams identity
4. **App Manifest**: Configure Teams app with bot capabilities

### Bot Adapter Pattern

```python
from botbuilder.core import TurnContext, ActivityHandler
from agent_framework.declarative import WorkflowFactory

class DistriPartnerBot(ActivityHandler):
    def __init__(self, workflow_factory: WorkflowFactory):
        self.factory = workflow_factory
        self.workflow = self.factory.create_workflow_from_yaml_path(
            "main-workflow.yaml"
        )
    
    async def on_message_activity(self, turn_context: TurnContext):
        user_message = turn_context.activity.text
        
        async for event in self.workflow.run_stream(user_message):
            if hasattr(event, 'text'):
                await turn_context.send_activity(event.text)
```

---

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Declarative Workflows Documentation](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/workflows/declarative)
- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
