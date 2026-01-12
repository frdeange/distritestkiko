# DistriPartner Platform

A multi-agent AI platform built with **Microsoft Agent Framework** using declarative YAML-based agent definitions. The platform enables intelligent customer support, campaign management, and partner operations through a coordinated system of specialized AI agents.

## 🎯 Objectives

- **Intelligent Orchestration**: Automatically route user requests to the most appropriate specialized agent
- **Declarative Agent Definitions**: Define agents using YAML files with PowerFx expressions for dynamic configuration
- **Multi-Agent Workflow**: Support complex hand-off scenarios between agents
- **Azure AI Integration**: Leverage Azure AI Foundry and Azure OpenAI for powerful LLM capabilities
- **Scalable Architecture**: Modular design allowing easy addition of new agents and capabilities

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interaction                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│         (Routes requests to specialized agents)              │
└─────────────────────────────────────────────────────────────┘
                    │                        │
          ┌────────┴────────┐      ┌────────┴────────┐
          ▼                 ▼      ▼                 ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     SUPPORT     │  │ CAMPAIGN        │  │ CAMPAIGN        │
│                 │  │ MANAGER         │  │ SUGGESTOR       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                    │
          ▼                    ├────────────────┬───────────────┐
┌─────────────────┐           ▼                ▼               ▼
│   TICKETING     │  ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│                 │  │   PROFILER      │ │ DATA        │ │COMMUNICATION│
└─────────────────┘  │                 │ │ COLLECTOR   │ │             │
          │          └─────────────────┘ └─────────────┘ └─────────────┘
          ▼
┌─────────────────┐
│   PROFILER /    │
│ DATA COLLECTOR  │
└─────────────────┘
```

## 📁 Project Structure

```
DistriPartnerSimplePlatform/
├── .devcontainer/
│   └── devcontainer.json      # Dev Container configuration
├── .env                        # Environment variables (create from .env.fake)
├── .env.fake                   # Template for environment variables
├── requirements.txt            # Python dependencies
├── DeclarativeAgents.md        # YAML schema documentation
├── src/
│   ├── run_agent.py            # Run individual agents
│   ├── run_workflow.py         # Run multi-agent workflow
│   └── agents/
│       ├── definitions/        # Agent YAML definitions
│       │   ├── orchestrator.yaml
│       │   ├── support.yaml
│       │   ├── ticketing.yaml
│       │   ├── profiler.yaml
│       │   ├── dataCollector.yaml
│       │   ├── campaignmanager.yaml
│       │   ├── campaignSuggestor.yaml
│       │   └── communication.yaml
│       └── workflow/
│           └── main-handoff.yaml
```

## 🚀 Getting Started

### Prerequisites

- **Azure Subscription** with Azure AI Foundry access
- **Azure OpenAI** deployment (GPT-4 or similar)
- **Docker** (for DevContainer)
- **VS Code** with DevContainers extension OR **GitHub Codespaces**

---

## 🐳 Running with DevContainer (Recommended)

### Option 1: VS Code + DevContainer

1. **Clone the repository**
   ```bash
   git clone https://github.com/frdeange/distritestkiko.git
   cd DistriPartnerSimplePlatform
   ```

2. **Open in VS Code**
   ```bash
   code .
   ```

3. **Reopen in Container**
   - Press `F1` or `Ctrl+Shift+P`
   - Type: `Dev Containers: Reopen in Container`
   - Wait for the container to build (first time takes ~5 minutes)

4. **Configure environment variables** (see [Environment Configuration](#-environment-configuration))

5. **Authenticate with Azure**
   ```bash
   az login
   ```

6. **Run the platform** (see [Execution](#-execution))

### Option 2: GitHub Codespaces ☁️

1. **Open in Codespaces**
   - Go to the repository on GitHub
   - Click the green **`<> Code`** button
   - Select the **`Codespaces`** tab
   - Click **`Create codespace on main`**

   Or use this direct link:
   
   [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=frdeange/distritestkiko)

2. **Wait for setup**
   - Codespaces will automatically build the DevContainer
   - All dependencies are installed via `postCreateCommand`

3. **Configure environment variables**
   ```bash
   cp .env.fake .env
   # Edit .env with your values
   ```

4. **Authenticate with Azure**
   ```bash
   az login --use-device-code
   ```

5. **Run the platform** (see [Execution](#-execution))

### DevContainer Features

The DevContainer includes:

| Feature | Description |
|---------|-------------|
| Python 3.12 | Main runtime environment |
| Azure CLI (`az`) | Azure resource management |
| Azure Developer CLI (`azd`) | Azure deployment automation |
| Docker-in-Docker | Container support within the DevContainer |
| Node.js | Frontend development support |
| .NET 8.0 SDK | Required for PowerFx expressions |

---

## ⚙️ Environment Configuration

### Required Variables

Create a `.env` file from the template:

```bash
cp .env.fake .env
```

Edit `.env` with your Azure credentials:

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_AI_PROJECT_ENDPOINT` | Azure AI Foundry project endpoint | `https://your-project.ai.azure.com` |
| `MODEL_DEPLOYMENT_COMPLEX` | Model for complex reasoning agents | `gpt-4.1` |
| `MODEL_DEPLOYMENT_STANDARD` | Model for standard agents | `gpt-4.1` |
| `MODEL_DEPLOYMENT_SIMPLE` | Model for simple task agents | `gpt-4.1` |

### Optional Variables (for full functionality)

| Variable | Description | Used By |
|----------|-------------|---------|
| `AZURE_AI_SEARCH_ENDPOINT` | Azure AI Search for RAG | Support agent |
| `AZURE_AI_SEARCH_KEY` | Search service admin key | Support agent |
| `VECTOR_STORE_SUPPORT` | Vector store ID for knowledge base | Support agent |
| `MCP_ENTRAID_URL` | EntraID MCP server URL | Profiler agent |
| `MCP_COSMOSDB_URL` | CosmosDB MCP server URL | DataCollector agent |
| `MCP_POWERSHELL_URL` | PowerShell MCP server URL | CampaignManager agent |
| `MCP_EMAIL_URL` | Email MCP server URL | Communication agent |

### Model Deployment Tiers

The platform supports three model tiers for cost optimization:

- **COMPLEX**: Advanced reasoning tasks (Orchestrator, Profiler) - use most capable model
- **STANDARD**: Moderate complexity (CampaignManager, DataCollector)
- **SIMPLE**: Straightforward tasks (Support, Ticketing, Communication)

---

## ▶️ Execution

### Run a Single Agent

Test individual agents in interactive mode:

```bash
cd src

# Run the orchestrator (default)
python run_agent.py

# Run a specific agent
python run_agent.py --agent support
python run_agent.py --agent ticketing
python run_agent.py --agent profiler

# List all available agents
python run_agent.py --list
```

### Run the Multi-Agent Workflow

Execute the complete hand-off workflow with all agents:

```bash
cd src

# Run interactive workflow
python run_workflow.py

# Run with debug output
python run_workflow.py --debug
```

### Workflow Interaction

1. Type your message and press **Enter**
2. The **Orchestrator** will analyze and route to the appropriate agent
3. Agents will hand off to specialists as needed
4. Say `adiós`, `gracias`, `thanks`, or `exit` to end the conversation

---

## 🤖 Available Agents

| Agent | Purpose | Hand-off Targets |
|-------|---------|------------------|
| **Orchestrator** | Routes requests to specialists | Support, CampaignManager |
| **Support** | Handles support inquiries | Ticketing |
| **Ticketing** | Manages support tickets | Profiler, DataCollector |
| **CampaignManager** | Executes campaigns on tenants | Profiler, DataCollector, Communication, CampaignSuggestor |
| **CampaignSuggestor** | Suggests campaign strategies | - |
| **Profiler** | Retrieves user profile data | - |
| **DataCollector** | Gathers tenant/subscription data | - |
| **Communication** | Sends notifications/emails | - |

---

## 📚 Documentation

- [DeclarativeAgents.md](DeclarativeAgents.md) - Complete YAML schema documentation for Microsoft Agent Framework

---

## 🛠️ Development

### Adding a New Agent

1. Create a new YAML file in `src/agents/definitions/`
2. Define the agent following the schema in [DeclarativeAgents.md](DeclarativeAgents.md)
3. Add the agent to `AVAILABLE_AGENTS` in `run_agent.py`
4. Add the agent to `AGENT_FILES` in `run_workflow.py`
5. Update `build_workflow()` to include hand-off routes

### Testing Changes

```bash
# Test individual agent
python run_agent.py --agent your_new_agent

# Test in workflow context
python run_workflow.py --debug
```

---

## 📋 Requirements

### Python Packages

```
agent-framework>=1.0.0b251223
agent-framework-declarative>=1.0.0b251223
azure-identity>=1.15.0
```

### System Requirements

- Python 3.12+
- .NET 8.0 SDK (for PowerFx expressions)
- Azure CLI (for authentication)

---

## 🔐 Authentication

The platform uses `DefaultAzureCredential` for Azure authentication, supporting:

1. **Azure CLI** - Run `az login` before starting
2. **Managed Identity** - When deployed on Azure
3. **Environment Variables** - `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`

For local development:

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
