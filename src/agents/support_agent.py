"""
Support Agent for the Microsoft Agent Framework workflow.

This agent handles technical questions and documentation requests using:
- MCP (Model Context Protocol) server for extended capabilities
- Azure AI Search for knowledge base queries
"""

from agent_framework import ai_function, MCPStreamableHTTPTool
from typing import Any, Dict, List, Optional
import os
import httpx
from .utils import create_azure_ai_client


class SupportAgent:
    """
    Support Agent that answers technical questions using MCP server and Azure AI Search.
    """

    def __init__(
        self,
        mcp_server_url: Optional[str] = None,
        ai_search_endpoint: Optional[str] = None,
        ai_search_api_key: Optional[str] = None,
        ai_search_index_name: Optional[str] = None,
    ):
        """
        Initialize the Support Agent.

        Args:
            mcp_server_url: URL of the MCP server
            ai_search_endpoint: Azure AI Search endpoint
            ai_search_api_key: Azure AI Search API key
            ai_search_index_name: Azure AI Search index name
        """
        self.mcp_server_url = mcp_server_url or os.getenv("MCP_SERVER_URL")
        self.ai_search_endpoint = ai_search_endpoint or os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.ai_search_api_key = ai_search_api_key or os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.ai_search_index_name = ai_search_index_name or os.getenv("AZURE_AI_SEARCH_INDEX_NAME")

        # Create the support agent
        chat_client = create_azure_ai_client()
        self.agent = chat_client.create_agent(
            name="support",
            instructions=self._get_instructions(),
            tools=self._setup_tools(),
        )

    def _get_instructions(self) -> str:
        """Get the system instructions for the support agent."""
        return """You are the Support Agent for a Microsoft Partner support system.

Your role is to provide technical assistance and answer questions about Microsoft products and services.

Capabilities:
- Answer technical questions using the knowledge base
- Search documentation using Azure AI Search
- Provide step-by-step guidance for common issues
- Use MCP server tools for extended functionality

Guidelines:
- Always search the knowledge base before answering
- Provide accurate, well-structured responses
- Include relevant documentation links when available
- If you cannot find the answer, be honest and suggest alternatives
- Use clear, professional language
- Format responses for readability (use bullet points, numbered lists, etc.)

When you've completed helping the user, let them know they'll be returned to the orchestrator."""

    def _setup_tools(self) -> List[Any]:
        """Set up tools for the support agent."""
        tools = []

        # Add MCP server tool if configured
        if self.mcp_server_url:
            try:
                mcp_tool = MCPStreamableHTTPTool(
                    name="mcp_server",
                    url=self.mcp_server_url,
                    description="Access MCP server for extended technical support capabilities",
                )
                tools.append(mcp_tool)
            except Exception as e:
                print(f"Warning: Could not initialize MCP tool: {e}")

        # Add AI Search function tool
        if self.ai_search_endpoint and self.ai_search_api_key:
            tools.append(self._create_search_tool())

        return tools

    def _create_search_tool(self):
        """Create an AI function for searching the knowledge base."""

        @ai_function
        async def search_knowledge_base(query: str, top: int = 5) -> Dict[str, Any]:
            """
            Search the Azure AI Search knowledge base for relevant information.

            Args:
                query: The search query
                top: Number of top results to return (default: 5)

            Returns:
                Search results with relevant documentation
            """
            if not self.ai_search_endpoint or not self.ai_search_api_key:
                return {
                    "error": "Azure AI Search is not configured",
                    "results": []
                }

            try:
                # Construct the search URL
                search_url = f"{self.ai_search_endpoint}/indexes/{self.ai_search_index_name}/docs/search"
                
                # Prepare search parameters
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.ai_search_api_key
                }
                
                payload = {
                    "search": query,
                    "top": top,
                    "queryType": "semantic",
                    "semanticConfiguration": "default",
                    "select": "title,content,url",
                }

                # Execute search request
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        search_url,
                        headers=headers,
                        json=payload,
                        params={"api-version": "2024-05-01-preview"}
                    )
                    response.raise_for_status()
                    
                    results = response.json()
                    return {
                        "success": True,
                        "count": results.get("@odata.count", 0),
                        "results": results.get("value", [])
                    }

            except Exception as e:
                return {
                    "error": f"Search failed: {str(e)}",
                    "results": []
                }

        return search_knowledge_base

    def get_agent(self):
        """Return the configured agent instance."""
        return self.agent


def create_support_agent(
    mcp_server_url: Optional[str] = None,
    ai_search_endpoint: Optional[str] = None,
    ai_search_api_key: Optional[str] = None,
    ai_search_index_name: Optional[str] = None,
):
    """
    Factory function to create and return a Support Agent.

    Args:
        mcp_server_url: URL of the MCP server
        ai_search_endpoint: Azure AI Search endpoint
        ai_search_api_key: Azure AI Search API key
        ai_search_index_name: Azure AI Search index name

    Returns:
        Configured agent for technical support
    """
    support = SupportAgent(
        mcp_server_url=mcp_server_url,
        ai_search_endpoint=ai_search_endpoint,
        ai_search_api_key=ai_search_api_key,
        ai_search_index_name=ai_search_index_name,
    )
    return support.get_agent()
