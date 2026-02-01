# DistriPartner Platform

A multi-agent AI platform built with **Microsoft Agent Framework** using **declarative YAML agent definitions** and **programmatic Python workflows**. The platform enables intelligent customer support through a coordinated system of specialized AI agents using the **HandoffBuilder** pattern.

## 🎯 Objectives

- **Intelligent Orchestration**: Automatically route user requests to specialized agents
- **Declarative Agent Definitions**: Define agents using YAML files with PowerFx expressions
- **Programmatic Workflows**: Use Python `HandoffBuilder` for reliable multi-agent orchestration
- **Azure AI Integration**: Leverage Azure AI Foundry and Azure OpenAI for LLM capabilities
- **Human-in-the-Loop**: Support multi-turn conversations with user interaction
- **Scalable Architecture**: Modular design for easy addition of new agents

## 📐 Architecture

The platform uses a **hybrid approach**:
- **Declarative YAML** for agent definitions (model, instructions, tools)
- **Programmatic Python** for workflow orchestration (`HandoffBuilder`)

```
┌─────────────────────────────────────────────────────────────┐
│                    DistriPartner Platform                    │
├─────────────────────────────────────────────────────────────┤
│  src/run_workflow.py                                        │
│  ├── --mode native    → handoff_native.py                   │
│  └── --mode controlled → handoff_controlled.py              │
├─────────────────────────────────────────────────────────────┤
│                 HandoffBuilder Workflow                      │
│                                                              │
│     ┌───────────────┐                                       │
│     │  ORCHESTRATOR │  (classifies user intent)             │
│     └───────┬───────┘                                       │
│             │                                                │
│    ┌────────┴────────┐                                      │
│    ▼                 ▼                                       │
│ ┌─────────┐     ┌───────────┐                               │
│ │ SUPPORT │────▶│ TICKETING │                               │
│ └─────────┘     └───────────┘                               │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Agent YAML Definitions                                      │
│  ├── orchestrator_native.yaml   (tool-call routing)         │
│  ├── orchestrator_controlled.yaml (JSON intent routing)     │
│  ├── support.yaml               (RAG + Microsoft Learn)     │
│  └── ticketing.yaml             (CosmosDB + Email)          │
├─────────────────────────────────────────────────────────────┤
│  External Services                                           │
│  • Azure OpenAI (GPT-4)                                      │
│  • Azure AI Search (Vector Store for RAG)                    │
│  • Microsoft Learn MCP Server                                │
│  • CosmosDB MCP Server                                       │
│  • Email MCP Server                                          │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Variants

The platform supports **two workflow modes** for evaluation:

| Mode | Description | Routing Mechanism |
|------|-------------|-------------------|
| **Native** | Decentralized routing | LLM calls `handoff_to_support()` / `handoff_to_ticketing()` tools |
| **Controlled** | Centralized routing | LLM returns JSON with Intent, Python routes based on Intent value |

## 📁 Project Structure

```
DistriPartnerSimplePlatform/
├── .devcontainer/
│   └── devcontainer.json         # Dev Container configuration
├── .env                           # Environment variables (create from .env.fake)
├── .env.fake                      # Template for environment variables
├── requirements.txt               # Python dependencies
├── DeclarativeAgents.md           # YAML schema documentation
├── README.md                      # This file
├── src/
│   ├── run_agent.py               # Run individual agents
│   ├── run_workflow.py            # Run multi-agent workflow
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models for responses
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── agents.py              # Agent loading from YAML
│   │   ├── common.py              # Shared utilities
│   │   ├── handoff_native.py      # Native workflow variant
│   │   └── handoff_controlled.py  # Controlled workflow variant
│   └── agents/
│       └── definitions/           # Agent YAML definitions
│           ├── orchestrator_native.yaml
│           ├── orchestrator_controlled.yaml
│           ├── support.yaml
│           ├── ticketing.yaml
│           ├── profiler.yaml
│           ├── dataCollector.yaml
│           ├── campaignmanager.yaml
│           ├── campaignSuggestor.yaml
│           └── communication.yaml
```

## 🚀 Getting Started

### Prerequisites

- **Azure Subscription** with Azure AI Foundry access
- **Azure OpenAI** deployment (GPT-4 or similar)
- **Docker** (for DevContainer)
- **VS Code** with DevContainers extension OR **GitHub Codespaces**

### Quick Start

1. **Clone and open in container**
   ```bash
   git clone https://github.com/frdeange/distritestkiko.git
   cd DistriPartnerSimplePlatform
   code .
   # Press F1 → "Dev Containers: Reopen in Container"
   ```

2. **Configure environment**
   ```bash
   cp .env.fake .env
   # Edit .env with your Azure credentials
   ```

3. **Authenticate with Azure**
   ```bash
   az login
   ```

4. **Run the workflow**
   ```bash
   cd src
   python run_workflow.py --mode native
   ```

---

## ▶️ Execution

### Run the Multi-Agent Workflow

```bash
cd src

# Run native mode (default) - LLM decides routing via tool calls
python run_workflow.py

# Run native mode with streaming responses
python run_workflow.py --mode native --streaming

# Run controlled mode - Python interprets JSON intent
python run_workflow.py --mode controlled

# Run controlled mode with streaming
python run_workflow.py --mode controlled --streaming
```

### Run Individual Agents

Test agents in isolation:

```bash
cd src

# Run orchestrator (native variant)
python run_agent.py --agent orchestrator-native

# Run orchestrator (controlled variant)
python run_agent.py --agent orchestrator-controlled

# Run support agent
python run_agent.py --agent support

# Run ticketing agent
python run_agent.py --agent ticketing

# List all available agents
python run_agent.py --list
```

### Workflow Interaction

1. Type your message and press **Enter**
2. The **Orchestrator** classifies intent and routes to the appropriate agent
3. **Support** agent handles technical questions, can escalate to **Ticketing**
4. **Ticketing** agent creates support tickets via CosmosDB and Email
5. Type `quit`, `exit`, or `goodbye` to end the conversation

---

## 🤖 Agent Overview

| Agent | Purpose | Tools | Hand-off Targets |
|-------|---------|-------|------------------|
| **Orchestrator** | Classifies intent, routes requests | - | Support, Ticketing |
| **Support** | First-level support, RAG search | file_search, Microsoft Learn MCP | Ticketing |
| **Ticketing** | Creates support tickets | CosmosDB MCP, Email MCP | Support |

---

## 🛠️ Development

### Adding a New Agent to the Workflow

1. **Create the agent YAML** in `src/agents/definitions/`:
   ```yaml
   kind: Agent
   name: NewAgent
   description: What this agent does
   instructions: |
     Detailed instructions for the agent...
   model:
     id: =Env.MODEL_DEPLOYMENT_SIMPLE
     provider: AzureAIAgentClient
     connection:
       kind: remote
       endpoint: =Env.AZURE_AI_PROJECT_ENDPOINT
   ```

2. **Add loading function** in `src/workflows/agents.py`:
   ```python
   async def load_new_agent(credential: DefaultAzureCredential) -> ChatAgent:
       return await load_agent_from_yaml("new_agent.yaml", credential)
   ```

3. **Register in HandoffBuilder** in `src/workflows/handoff_native.py`:
   ```python
   async def build_native_workflow(credential):
       new_agent = await load_new_agent(credential)
       
       workflow = (
           HandoffBuilder(
               name="distripartner_native",
               participants=[orchestrator, support, ticketing, new_agent],  # Add here
           )
           .with_start_agent(orchestrator)
           .add_handoff(orchestrator, [support, ticketing, new_agent])  # Add handoff
           .add_handoff(new_agent, [orchestrator])  # Define return path
           .build()
       )
   ```

4. **Update Orchestrator instructions** in `orchestrator_native.yaml`:
   ```yaml
   instructions: |
     ...
     ### handoff_to_new_agent
     Use this tool when the user needs [describe when to use]...
   ```

5. **Add to run_agent.py** for individual testing:
   ```python
   AVAILABLE_AGENTS = {
       ...
       "new-agent": "new_agent.yaml",
   }
   ```

### HandoffBuilder API Reference

```python
from agent_framework import HandoffBuilder

workflow = (
    HandoffBuilder(
        name="workflow_name",
        participants=[agent1, agent2, agent3],  # All agents in the workflow
        description="Optional description",
    )
    .with_start_agent(triage_agent)  # First agent to receive messages
    .add_handoff(source, [targets])  # Define routing paths
    .with_termination_condition(
        lambda conv: "welcome" in conv[-1].text.lower()  # When to stop
    )
    .build()
)
```

---

## ⚙️ Environment Configuration

Create `.env` from template:

```bash
cp .env.fake .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_AI_PROJECT_ENDPOINT` | Azure AI Foundry project endpoint | `https://your-project.ai.azure.com` |
| `MODEL_DEPLOYMENT_COMPLEX` | Model for complex reasoning | `gpt-4.1` |
| `MODEL_DEPLOYMENT_SIMPLE` | Model for simple tasks | `gpt-4.1` |

### Optional Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `VECTOR_STORE_SUPPORT` | Vector store ID for RAG | Support agent |
| `MCP_LEARN_URL` | Microsoft Learn MCP URL | Support agent |
| `MCP_COSMOSDB_URL` | CosmosDB MCP URL | Ticketing agent |
| `MCP_EMAIL_URL` | Email MCP URL | Ticketing agent |

---

## 📚 Technical Details

### Why Programmatic Workflows?

The platform evolved from declarative YAML workflows to programmatic Python workflows because:

1. **PowerFx Limitations**: The PowerFx Python wrapper has bugs with nested property access (`Local.X.Y` fails when `Y` is None)
2. **Flexibility**: Python code allows custom routing logic, logging, and error handling
3. **Debugging**: Easier to debug Python than declarative YAML expressions
4. **Reliability**: HandoffBuilder is a stable, well-tested pattern

### Workflow Architecture

The HandoffBuilder pattern provides:
- **Decentralized routing**: Agents decide handoffs via tool calls
- **Human-in-the-loop**: Workflow pauses for user input
- **Multi-turn conversations**: Full conversation history maintained
- **Termination conditions**: Custom logic to end workflows

---

## 📋 Requirements

### Python Packages

```
agent-framework>=1.0.0b260130
agent-framework-declarative>=1.0.0b260130
agent-framework-azure-ai>=1.0.0b260130
agent-framework-azure-ai-search>=1.0.0b260130
azure-identity>=1.15.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### System Requirements

- Python 3.12+
- .NET 8.0 SDK (for PowerFx expressions in YAML)
- Azure CLI (for authentication)

---

## 🔐 Authentication

The platform uses `DefaultAzureCredential`:

```bash
# Interactive login
az login

# For Codespaces/remote environments
az login --use-device-code
```

---

## 📄 License

This project is for demonstration purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📞 Support

For issues or questions, please open an issue in the repository.
