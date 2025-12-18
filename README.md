# Microsoft Agent Framework - Support System Workflow

A comprehensive agent workflow system built with the Microsoft Agent Framework, implementing an orchestration pattern for managing support, ticketing, database queries, and campaign management.

## Overview

This project implements a multi-agent system with the following specialized agents:

- **Orchestrator Agent**: Routes user interactions to appropriate specialized agents using a returnToPrevious handoff pattern
- **Support Agent**: Handles technical questions using MCP server and Azure AI Search
- **Ticket Agent**: Creates and manages support tickets in Microsoft Partner Center
- **Database Agent**: Queries Azure Cosmos DB for data retrieval
- **Campaign Agent**: Executes marketing campaigns and distributor actions
- **Notification Agent**: Skeleton implementation for email notifications (future development)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│          (Routes to specialized agents)                      │
└───────┬──────────┬──────────┬──────────┬───────────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌──────────┐ ┌─────────┐
   │Support │ │Ticket  │ │Database  │ │Campaign │
   │Agent   │ │Agent   │ │Agent     │ │Agent    │
   └────────┘ └────────┘ └──────────┘ └─────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌──────────┐ ┌─────────┐
   │MCP +   │ │Partner │ │Cosmos DB │ │Campaign │
   │AI      │ │Center  │ │          │ │System   │
   │Search  │ │API     │ │          │ │         │
   └────────┘ └────────┘ └──────────┘ └─────────┘
```

## Features

### Orchestrator Agent
- Intelligent routing based on user intent
- returnToPrevious handoff pattern for seamless UX
- Clear handoff descriptions and context management

### Support Agent
- MCP server integration for extended capabilities
- Azure AI Search for knowledge base queries
- Semantic search with configurable result limits
- Professional technical assistance

### Ticket Agent
- OAuth2 authentication with Partner Center API
- Create and track support tickets
- Priority-based ticket management
- Real-time ticket status checking

### Database Agent
- Azure Cosmos DB integration
- SQL-like query support
- Customer lookup by ID or name
- Historical data retrieval
- Cross-partition query support

### Campaign Agent
- Campaign creation and management
- Performance metrics tracking
- Budget management
- Distributor-specific action execution
- Multiple campaign types support

### Notification Agent (Skeleton)
- Placeholder for future email notification functionality
- Azure Communication Service integration planned

## Installation

1. Clone the repository:
```bash
git clone https://github.com/frdeange/distritestkiko.git
cd distritestkiko
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Create a `.env` file based on `.env.example` and configure the following:

### Required Configuration

#### Azure OpenAI
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Optional Configuration

#### Azure AI Search (for Support Agent)
```env
AZURE_AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_AI_SEARCH_API_KEY=your-search-api-key-here
AZURE_AI_SEARCH_INDEX_NAME=your-index-name
```

#### Azure Cosmos DB (for Database Agent)
```env
COSMOS_DB_ENDPOINT=https://your-cosmosdb.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmosdb-key-here
COSMOS_DB_DATABASE_NAME=your-database-name
COSMOS_DB_CONTAINER_NAME=your-container-name
```

#### Microsoft Partner Center (for Ticket Agent)
```env
PARTNER_CENTER_API_ENDPOINT=https://api.partnercenter.microsoft.com
PARTNER_CENTER_TENANT_ID=your-tenant-id-here
PARTNER_CENTER_CLIENT_ID=your-client-id-here
PARTNER_CENTER_CLIENT_SECRET=your-client-secret-here
```

#### MCP Server (for Support Agent)
```env
MCP_SERVER_URL=http://localhost:8080
MCP_SERVER_API_KEY=your-mcp-api-key-here
```

#### Azure Communication Service (for Notification Agent - Future)
```env
AZURE_COMMUNICATION_CONNECTION_STRING=your-connection-string-here
AZURE_COMMUNICATION_SENDER_EMAIL=noreply@your-domain.com
```

## Usage

### Running the Application

```bash
python src/main.py
```

### Using Individual Agents

```python
from agents import (
    create_orchestrator_agent,
    create_support_agent,
    create_ticket_agent,
    create_database_agent,
    create_campaign_agent,
)

# Create specialized agents
support_agent = create_support_agent()
ticket_agent = create_ticket_agent()
database_agent = create_database_agent()
campaign_agent = create_campaign_agent()

# Create orchestrator with handoffs
orchestrator = create_orchestrator_agent(
    support_agent=support_agent,
    ticket_agent=ticket_agent,
    database_agent=database_agent,
    campaign_agent=campaign_agent,
)
```

### Example Interactions

#### Technical Support
```
User: "How do I configure Azure AD authentication?"
→ Routed to Support Agent
→ Searches knowledge base
→ Provides step-by-step guidance
→ Returns to Orchestrator
```

#### Ticket Creation
```
User: "I need to report a critical system issue"
→ Routed to Ticket Agent
→ Collects issue details
→ Creates ticket in Partner Center
→ Provides ticket ID
→ Returns to Orchestrator
```

#### Database Query
```
User: "Find customer information for ID 12345"
→ Routed to Database Agent
→ Queries Cosmos DB
→ Returns customer details
→ Returns to Orchestrator
```

#### Campaign Management
```
User: "Create a new email campaign for Q1 2024"
→ Routed to Campaign Agent
→ Collects campaign details
→ Creates and schedules campaign
→ Provides campaign ID and status
→ Returns to Orchestrator
```

## Development

### Project Structure

```
distritestkiko/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator_agent.py
│   │   ├── support_agent.py
│   │   ├── ticket_agent.py
│   │   ├── database_agent.py
│   │   ├── campaign_agent.py
│   │   └── notification_agent.py
│   └── main.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Adding New Agents

1. Create a new agent file in `src/agents/`
2. Implement the agent class with appropriate tools
3. Add factory function for agent creation
4. Update `__init__.py` to export the new agent
5. Add handoff in orchestrator if needed

### Extending Existing Agents

Each agent has:
- **Instructions**: System prompt defining agent behavior
- **Tools**: AI functions for specific capabilities
- **Configuration**: Environment-based settings

To add new capabilities:
1. Add new AI functions using `@ai_function` decorator
2. Register tools in agent's `_setup_tools()` method
3. Update agent instructions to describe new capabilities

## Design Patterns

### Handoff Pattern: returnToPrevious
All agents use the `returnToPrevious=True` pattern, ensuring:
- Users return to orchestrator after specialist completes task
- Smooth conversation flow
- Centralized routing control

### Bidirectional Handoffs
Database Agent supports handoffs from:
- Ticket Agent (for data lookup during ticket creation)
- Campaign Agent (for campaign-related data queries)

### Tool-Based Architecture
Agents use `@ai_function` decorated tools for:
- Clear capability definition
- Type-safe parameters
- Automatic schema generation
- Easy testing and maintenance

## Testing

(To be implemented)

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests
pytest
```

## Troubleshooting

### Common Issues

**Agent not responding**
- Verify Azure OpenAI credentials in `.env`
- Check API endpoint and deployment name
- Ensure API version is supported

**MCP Server connection failed**
- Verify MCP_SERVER_URL is correct
- Check MCP server is running
- Validate API key if required

**Database queries failing**
- Verify Cosmos DB credentials
- Check database and container names
- Ensure cross-partition queries are enabled

**Ticket creation errors**
- Verify Partner Center credentials
- Check OAuth2 token generation
- Validate API endpoint and permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues and questions:
- Open an issue on GitHub
- Contact the development team

## Roadmap

- [ ] Complete Notification Agent implementation
- [ ] Add comprehensive test coverage
- [ ] Implement UI/Web interface
- [ ] Add monitoring and logging
- [ ] Performance optimization
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Enhanced security features

## Acknowledgments

Built with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
