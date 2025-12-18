"""
Utility functions for creating chat clients and other common functionality.
"""

import os
from typing import Optional


def create_azure_ai_client(
    project_endpoint: Optional[str] = None,
    model_deployment_name: Optional[str] = None,
):
    """
    Create an Azure AI chat client for use with agents.
    
    Args:
        project_endpoint: Azure AI project endpoint (defaults to env var)
        model_deployment_name: Model deployment name (defaults to env var)
    
    Returns:
        Configured AzureAIClient instance
        
    Note:
        This requires proper Azure credentials to be configured.
        For development/testing without credentials, agents may need to be mocked.
    """
    from agent_framework_azure_ai import AzureAIClient
    from azure.identity.aio import DefaultAzureCredential
    
    endpoint = project_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
    model = model_deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    if not endpoint:
        raise ValueError(
            "Azure OpenAI endpoint not configured. "
            "Please set AZURE_OPENAI_ENDPOINT in your .env file or pass project_endpoint parameter."
        )
    
    # Create client with default Azure credentials
    client = AzureAIClient(
        project_endpoint=endpoint,
        model_deployment_name=model,
        credential=DefaultAzureCredential(),
    )
    
    return client
