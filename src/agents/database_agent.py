"""
Database Agent for the Microsoft Agent Framework workflow.

This agent handles queries to Azure Cosmos DB and provides data retrieval
capabilities for the system.
"""

from agent_framework import ChatAgent, ai_function, HandoffBuilder
from typing import Any, Dict, List, Optional
import os
from azure.cosmos import CosmosClient, exceptions


class DatabaseAgent:
    """
    Database Agent that queries Azure Cosmos DB for information.
    Supports bidirectional handoff with Ticket and Campaign agents.
    """

    def __init__(
        self,
        cosmos_endpoint: Optional[str] = None,
        cosmos_key: Optional[str] = None,
        database_name: Optional[str] = None,
        container_name: Optional[str] = None,
    ):
        """
        Initialize the Database Agent.

        Args:
            cosmos_endpoint: Azure Cosmos DB endpoint
            cosmos_key: Azure Cosmos DB key
            database_name: Database name
            container_name: Container name
        """
        self.cosmos_endpoint = cosmos_endpoint or os.getenv("COSMOS_DB_ENDPOINT")
        self.cosmos_key = cosmos_key or os.getenv("COSMOS_DB_KEY")
        self.database_name = database_name or os.getenv("COSMOS_DB_DATABASE_NAME")
        self.container_name = container_name or os.getenv("COSMOS_DB_CONTAINER_NAME")
        
        self._client = None
        self._database = None
        self._container = None

        # Create the database agent
        self.agent = ChatAgent(
            name="database",
            model="azure-openai",
            instructions=self._get_instructions(),
            tools=self._setup_tools(),
        )

    def _get_instructions(self) -> str:
        """Get the system instructions for the database agent."""
        return """You are the Database Agent for a Microsoft Partner support system.

Your role is to query and retrieve information from the Azure Cosmos DB database.

Capabilities:
- Query customer information
- Retrieve historical records
- Search for specific data points
- Generate data summaries and reports
- Filter and aggregate data

Guidelines:
- Always validate query parameters before executing
- Return results in a clear, structured format
- Handle errors gracefully and inform the user
- Protect sensitive information (mask PII when necessary)
- Provide context with query results
- Suggest relevant follow-up queries when appropriate

Available query types:
- Customer lookup by ID or name
- Transaction history
- Support ticket history
- Campaign information
- General data queries using SQL-like syntax

When you've completed the database query, let them know they'll be returned to the orchestrator."""

    def _setup_tools(self) -> list:
        """Set up tools for the database agent."""
        return [
            self._create_query_tool(),
            self._create_customer_lookup_tool(),
            self._create_history_tool(),
        ]

    def _get_cosmos_client(self):
        """Initialize and return Cosmos DB client."""
        if not self._client:
            if self.cosmos_endpoint and self.cosmos_key:
                self._client = CosmosClient(self.cosmos_endpoint, self.cosmos_key)
                self._database = self._client.get_database_client(self.database_name)
                self._container = self._database.get_container_client(self.container_name)
        return self._container

    def _create_query_tool(self):
        """Create an AI function for general database queries."""

        @ai_function
        async def query_database(
            query: str,
            parameters: Optional[List[Dict[str, Any]]] = None
        ) -> Dict[str, Any]:
            """
            Execute a query against the Cosmos DB database.

            Args:
                query: SQL-like query string
                parameters: Optional query parameters

            Returns:
                Query results
            """
            if not self.cosmos_endpoint or not self.cosmos_key:
                return {
                    "success": False,
                    "error": "Cosmos DB is not configured",
                    "results": []
                }

            try:
                container = self._get_cosmos_client()
                
                # Execute query
                items = list(container.query_items(
                    query=query,
                    parameters=parameters or [],
                    enable_cross_partition_query=True
                ))

                return {
                    "success": True,
                    "count": len(items),
                    "results": items
                }

            except exceptions.CosmosHttpResponseError as e:
                return {
                    "success": False,
                    "error": f"Database query failed: {e.message}",
                    "results": []
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                    "results": []
                }

        return query_database

    def _create_customer_lookup_tool(self):
        """Create an AI function for customer lookups."""

        @ai_function
        async def lookup_customer(
            customer_id: Optional[str] = None,
            customer_name: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Look up customer information by ID or name.

            Args:
                customer_id: Customer ID to look up
                customer_name: Customer name to search for

            Returns:
                Customer information
            """
            if not self.cosmos_endpoint or not self.cosmos_key:
                return {
                    "success": False,
                    "error": "Cosmos DB is not configured",
                    "customer": None
                }

            try:
                container = self._get_cosmos_client()
                
                # Build query based on parameters
                if customer_id:
                    query = "SELECT * FROM c WHERE c.customer_id = @customer_id"
                    parameters = [{"name": "@customer_id", "value": customer_id}]
                elif customer_name:
                    query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.name), LOWER(@customer_name))"
                    parameters = [{"name": "@customer_name", "value": customer_name}]
                else:
                    return {
                        "success": False,
                        "error": "Either customer_id or customer_name must be provided",
                        "customer": None
                    }

                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))

                if items:
                    return {
                        "success": True,
                        "count": len(items),
                        "customers": items
                    }
                else:
                    return {
                        "success": True,
                        "count": 0,
                        "message": "No customer found with the given criteria"
                    }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Customer lookup failed: {str(e)}",
                    "customer": None
                }

        return lookup_customer

    def _create_history_tool(self):
        """Create an AI function for retrieving historical data."""

        @ai_function
        async def get_history(
            entity_type: str,
            entity_id: str,
            limit: int = 10
        ) -> Dict[str, Any]:
            """
            Retrieve historical records for a specific entity.

            Args:
                entity_type: Type of entity (customer, ticket, campaign, etc.)
                entity_id: ID of the entity
                limit: Maximum number of records to return

            Returns:
                Historical records
            """
            if not self.cosmos_endpoint or not self.cosmos_key:
                return {
                    "success": False,
                    "error": "Cosmos DB is not configured",
                    "history": []
                }

            try:
                container = self._get_cosmos_client()
                
                # Query for historical records
                query = """
                    SELECT * FROM c 
                    WHERE c.entity_type = @entity_type 
                    AND c.entity_id = @entity_id 
                    ORDER BY c.timestamp DESC
                    OFFSET 0 LIMIT @limit
                """
                
                parameters = [
                    {"name": "@entity_type", "value": entity_type},
                    {"name": "@entity_id", "value": entity_id},
                    {"name": "@limit", "value": limit}
                ]

                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))

                return {
                    "success": True,
                    "count": len(items),
                    "history": items
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"History retrieval failed: {str(e)}",
                    "history": []
                }

        return get_history

    def get_agent(self) -> ChatAgent:
        """Return the configured ChatAgent instance."""
        return self.agent


def create_database_agent(
    cosmos_endpoint: Optional[str] = None,
    cosmos_key: Optional[str] = None,
    database_name: Optional[str] = None,
    container_name: Optional[str] = None,
) -> ChatAgent:
    """
    Factory function to create and return a Database Agent.

    Args:
        cosmos_endpoint: Azure Cosmos DB endpoint
        cosmos_key: Azure Cosmos DB key
        database_name: Database name
        container_name: Container name

    Returns:
        Configured ChatAgent for database queries
    """
    database = DatabaseAgent(
        cosmos_endpoint=cosmos_endpoint,
        cosmos_key=cosmos_key,
        database_name=database_name,
        container_name=container_name,
    )
    return database.get_agent()
