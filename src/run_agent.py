# =============================================================================
# DistriPartner Platform - Agent Runner
# =============================================================================
# Script to load and run declarative agents from YAML definitions.
# Uses Microsoft Agent Framework with Azure AI Foundry.
#
# Usage:
#   python run_agent.py                    # Runs orchestrator (default)
#   python run_agent.py --agent support    # Runs specific agent
#   python run_agent.py --list             # List available agents
#
# Requirements:
#   - Copy .env.fake to .env and fill in your Azure AI credentials
#   - Run: az login (for Azure CLI authentication)
#   - Install: pip install -r requirements.txt
# =============================================================================

import asyncio
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agent_framework_declarative import AgentFactory
from azure.identity.aio import DefaultAzureCredential


# Available agents and their YAML files
AGENTS_DIR = Path(__file__).parent / "agents" / "definitions"
AVAILABLE_AGENTS = {
    "orchestrator": "orchestrator.yaml",
    "support": "support.yaml",
    "ticketing": "ticketing.yaml",
    "profiler": "profiler.yaml",
    "datacollector": "dataCollector.yaml",
    "campaignmanager": "campaignmanager.yaml",
    "campaignsuggestor": "campaignSuggestor.yaml",
    "communication": "communication.yaml",
}


def list_agents():
    """List all available agents."""
    print("\n📋 Available Agents:")
    print("-" * 50)
    for name, filename in AVAILABLE_AGENTS.items():
        yaml_path = AGENTS_DIR / filename
        status = "✅" if yaml_path.exists() else "❌"
        print(f"  {status} {name:<20} ({filename})")
    print("-" * 50)
    print("\nUsage: python run_agent.py --agent <agent_name>")
    print("       python run_agent.py  (defaults to orchestrator)\n")


async def run_agent(agent_name: str):
    """Load and run an agent interactively."""
    
    if agent_name not in AVAILABLE_AGENTS:
        print(f"❌ Unknown agent: {agent_name}")
        list_agents()
        return
    
    yaml_file = AVAILABLE_AGENTS[agent_name]
    yaml_path = AGENTS_DIR / yaml_file
    
    if not yaml_path.exists():
        print(f"❌ Agent file not found: {yaml_path}")
        return
    
    print(f"\n🤖 Loading agent: {agent_name}")
    print(f"   File: {yaml_path}")
    print("-" * 50)
    
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
        # Create agent factory with Azure credentials
        # safe_mode=False allows PowerFx expressions to read environment variables
        factory = AgentFactory(
            client_kwargs={
                "credential": credential,
                "project_endpoint": os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            },
            env_file_path=str(Path(__file__).parent.parent / ".env"),
            safe_mode=False
        )
        
        # Load agent from YAML
        agent = factory.create_agent_from_yaml_path(yaml_path)
        
        print(f"✅ Agent '{agent_name}' loaded successfully!")
        print("\n💬 Interactive Chat Mode")
        print("   Type your message and press Enter.")
        print("   Type 'quit' or 'exit' to stop.\n")
        print("=" * 50)
        
        # Interactive chat loop
        async with agent:
            while True:
                try:
                    user_input = input("\n👤 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ["quit", "exit", "q"]:
                        print("\n👋 Goodbye!")
                        break
                    
                    print("\n🤖 Agent: ", end="", flush=True)
                    response = await agent.run(user_input)
                    print(response)
                    
                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted. Goodbye!")
                    break
                    
    except Exception as e:
        print(f"\n❌ Error loading agent: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Copied .env.fake to .env with valid credentials")
        print("   2. Logged in with: az login")
        print("   3. Installed requirements: pip install -r requirements.txt")
        raise
    
    finally:
        await credential.close()


def main():
    parser = argparse.ArgumentParser(
        description="Run DistriPartner declarative agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_agent.py                    # Run orchestrator (default)
  python run_agent.py --agent support    # Run support agent
  python run_agent.py --list             # List available agents
        """
    )
    parser.add_argument(
        "--agent", "-a",
        default="orchestrator",
        help="Name of the agent to run (default: orchestrator)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available agents"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_agents()
        return
    
    print("\n" + "=" * 50)
    print("  DistriPartner Platform - Agent Runner")
    print("=" * 50)
    
    asyncio.run(run_agent(args.agent))


if __name__ == "__main__":
    main()
