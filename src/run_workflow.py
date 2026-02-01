# =============================================================================
# DistriPartner Platform - Workflow Runner
# =============================================================================
# Entry point to run the programmatic HandoffBuilder workflow.
# Supports both Native and Controlled variants.
#
# Usage:
#   python run_workflow.py                     # Runs native mode (default)
#   python run_workflow.py --mode native       # Explicit native mode
#   python run_workflow.py --mode controlled   # Controlled mode
#   python run_workflow.py --streaming         # With streaming responses
#
# Requirements:
#   - Copy .env.fake to .env and fill in your Azure AI credentials
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

from azure.identity.aio import DefaultAzureCredential
from workflows.handoff_native import (
    run_native_workflow_interactive,
    run_native_workflow_streaming,
)
from workflows.handoff_controlled import (
    run_controlled_workflow_interactive,
    run_controlled_workflow_streaming,
)


async def run_workflow(mode: str = "native", streaming: bool = False) -> None:
    """
    Run the DistriPartner workflow.
    
    Args:
        mode: Either "native" or "controlled"
        streaming: Whether to use streaming responses
    """
    # Check required environment variables
    required_vars = ["AZURE_AI_PROJECT_ENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Copy .env.fake to .env and fill in your values.")
        return
    
    # Create credential for Azure authentication
    credential = DefaultAzureCredential()
    
    try:
        if mode == "native":
            if streaming:
                await run_native_workflow_streaming(credential)
            else:
                await run_native_workflow_interactive(credential)
        elif mode == "controlled":
            if streaming:
                await run_controlled_workflow_streaming(credential)
            else:
                await run_controlled_workflow_interactive(credential)
        else:
            print(f"❌ Unknown mode: {mode}")
            print("   Valid modes: native, controlled")
            return
            
    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Copied .env.fake to .env with valid credentials")
        print("   2. Logged in with: az login")
        print("   3. Installed requirements: pip install -r requirements.txt")
        raise
    
    finally:
        await credential.close()


def main():
    parser = argparse.ArgumentParser(
        description="Run DistriPartner HandoffBuilder workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow Modes:
  native      Orchestrator uses auto-generated handoff tool calls.
              Routing is decentralized - LLM decides which tool to call.
              
  controlled  Orchestrator returns JSON with Intent field.
              Python code interprets intent and logs routing decisions.

Examples:
  python run_workflow.py                       # Run native mode
  python run_workflow.py --mode controlled     # Run controlled mode
  python run_workflow.py --streaming           # With streaming responses
  python run_workflow.py --mode native --streaming

For more information, see the documentation in README.md
        """
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["native", "controlled"],
        default="native",
        help="Workflow mode: native (tool calls) or controlled (JSON intent)"
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
    print(f"  Mode: {args.mode}")
    print(f"  Streaming: {args.streaming}")
    print("=" * 60)
    
    asyncio.run(run_workflow(args.mode, args.streaming))


if __name__ == "__main__":
    main()
