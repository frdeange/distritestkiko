# DistriPartner Platform

A multi-agent AI platform built with **Microsoft Agent Framework** using the **HandoffBuilder** pattern for LLM-driven agent orchestration. The platform enables intelligent customer support through a coordinated system of specialized AI agents deployed as a Teams bot.

## Architecture

The platform uses **HandoffBuilder** for multi-agent orchestration — agents decide when to route to other agents via LLM tool calls (`handoff_to_<AgentName>`).

```
┌─────────────────────────────────────────────────────────────┐
│                    DistriPartner Platform                    │
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
│ └─────────┘     └─────┬─────┘                               │
│                   ┌───┴───┐                                  │
│                   ▼       ▼                                  │
│            ┌────────┐ ┌──────────────┐                      │
│            │DATAGATH│ │COMMUNICATION │                      │
│            │(auto)  │ │   (auto)     │                      │
│            └────────┘ └──────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│  External Services                                           │
│  • Azure OpenAI (GPT-4.1 / GPT-4.1-mini)                   │
│  • Azure MCP Server (CosmosDB, EntraID, Email)              │
│  • Microsoft Learn MCP Server                                │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
DistriPartnerSimplePlatform/
├── docs/
│   ├── ARCHITECTURE.md            # Full architecture reference
│   └── support-kb/                # Knowledge base articles
├── scripts/
│   ├── setup_ai_search.py         # Azure AI Search provisioning
│   └── setup_cosmos.py            # CosmosDB provisioning
├── src/
│   ├── orchestration/
│   │   └── handoff.py             # HandoffBuilder workflow factory
│   ├── agents/
│   │   ├── response_models.py     # Pydantic structured output models
│   │   └── instructions/          # Agent instruction YAML files
│   │       ├── orchestrator.yaml
│   │       ├── support.yaml
│   │       ├── ticketing.yaml
│   │       ├── datagatherer.yaml
│   │       └── communication.yaml
│   ├── backend/
│   │   ├── bot.py                 # Teams bot (M365 Agents SDK)
│   │   ├── config.py              # Environment configuration
│   │   ├── cosmos_store.py        # CosmosDB storage helpers
│   │   ├── main.py                # Application entry point
│   │   ├── start_server.py        # AIOHTTP server startup
│   │   ├── workflow_manager.py    # Per-conversation workflow sessions
│   │   └── workflow_state.py      # CosmosDB state storage
│   └── frontend/
│       ├── DistriPartnerSupport.zip # Pre-packaged Teams app
│       └── teams-manifest/        # Teams app manifest
├── tests/
│   └── test_agent_schema.py       # Schema validation tests
├── Dockerfile
├── requirements.txt
└── README.md
```

## Agents

| Agent | Purpose | Model | Mode |
|-------|---------|-------|------|
| **Orchestrator** | Classifies intent, routes requests | gpt-4.1-mini | Interactive |
| **Support** | First-level troubleshooting, RAG search | gpt-4.1 | Interactive |
| **Ticketing** | Creates support tickets in CosmosDB | gpt-4.1 | Interactive |
| **DataGatherer** | Retrieves user profile (EntraID + CosmosDB) | gpt-4.1-mini | Autonomous |
| **Communication** | Sends email notifications | gpt-4.1-mini | Autonomous |

## Getting Started

### Prerequisites

- **Azure Subscription** with Azure AI Foundry access
- **Azure OpenAI** deployment (GPT-4.1 or similar)
- **Python 3.12+**

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/frdeange/distritestkiko.git
   cd DistriPartnerSimplePlatform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.fake .env
   # Edit .env with your Azure credentials
   ```

4. **Authenticate with Azure**
   ```bash
   az login
   ```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `AZURE_AI_PROJECT_ENDPOINT` | Azure AI Foundry project endpoint |
| `MODEL_DEPLOYMENT_COMPLEX` | Model for complex reasoning (e.g., `gpt-4.1`) |
| `MODEL_DEPLOYMENT_STANDARD` | Model for standard tasks (e.g., `gpt-4.1`) |
| `MODEL_DEPLOYMENT_SIMPLE` | Model for simple tasks (e.g., `gpt-4.1`) |
| `MODEL_DEPLOYMENT_MINI` | Model for lightweight tasks (e.g., `gpt-4.1-mini`) |

### MCP Servers

| Variable | Used By | Purpose |
|----------|---------|---------|
| `MCP_LEARN_URL` | Support | Microsoft Learn documentation search |
| `MCP_COSMOSDB_URL` | DataGatherer, Ticketing | CosmosDB data access |
| `MCP_ENTRAID_URL` | DataGatherer | User identity lookup |
| `MCP_EMAIL_URL` | Communication | Email notifications |

## Adding a New Agent

1. Create instruction YAML in `src/agents/instructions/`
2. Add Pydantic response model in `src/agents/response_models.py`
3. Register in `src/orchestration/handoff.py` with HandoffBuilder
4. Update Orchestrator instructions with new handoff tool description

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed instructions.

## Deployment

The platform deploys as a Docker container to Azure Container Apps:

```bash
docker build -t distripartner .
```

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
