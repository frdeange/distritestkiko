# =============================================================================
# DistriPartner Platform - Workflow Runner
# =============================================================================
# Entry point to run the declarative multi-agent workflow.
# Uses AzureOpenAIResponsesClient + WorkflowFactory with YAML-defined routing.
#
# Usage:
#   python run_workflow.py                  # Run interactive workflow
#   python run_workflow.py --streaming      # With streaming responses
#
# Requirements:
#   - Copy .env.example to .env and fill in your Azure AI credentials
#   - Run: az login (for Azure CLI authentication)
#   - Install: pip install -r requirements.txt
# =============================================================================

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add src to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from azure.identity import AzureCliCredential
from workflows.declarative import (
    run_declarative_workflow_streaming,
    run_declarative_workflow_interactive,
)


async def run_workflow(streaming: bool = False) -> None:
    """
    Run the DistriPartner declarative workflow.

    Args:
        streaming: Whether to use streaming responses
    """
    # Check required environment variables
    required_vars = ["AZURE_AI_PROJECT_ENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Copy .env.example to .env and fill in your values.")
        return

    credential = AzureCliCredential()
    try:
        if streaming:
            await run_declarative_workflow_streaming(credential)
        else:
            await run_declarative_workflow_interactive(credential)
    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Copied .env.example to .env with valid credentials")
        print("   2. Logged in with: az login")
        print("   3. Installed requirements: pip install -r requirements.txt")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Run DistriPartner declarative multi-agent workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Runs the declarative workflow using AzureOpenAIResponsesClient + WorkflowFactory.
Routing is defined in workflow.yaml using ConditionGroup and externalLoop.

Examples:
  python run_workflow.py                # Run interactive workflow
  python run_workflow.py --streaming    # With streaming responses

For more information, see the documentation in README.md
        """
    )
    parser.add_argument(
        "--streaming", "-s",
        action="store_true",
        help="Enable streaming responses for real-time output"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  DistriPartner Platform - Workflow Runner")
    print("=" * 60)
    print(f"  Streaming: {args.streaming}")
    print("=" * 60)

    asyncio.run(run_workflow(args.streaming))


if __name__ == "__main__":
    main()
