# =============================================================================
# DistriPartner Platform - Agent Schema Validation Tests
# =============================================================================
# Tests to validate that agent YAML files conform to the required schema.
# Ensures all agents have proper structure, required fields, and outputSchema.
#
# Usage:
#   pytest tests/test_agent_schema.py -v
# =============================================================================

import os
import yaml
import pytest
from pathlib import Path
from typing import Any


# Path to agent definitions
AGENTS_DIR = Path(__file__).parent.parent / "src" / "agents" / "definitions"
WORKFLOW_DIR = Path(__file__).parent.parent / "src" / "agents" / "workflow"

# Required fields for all agents
REQUIRED_AGENT_FIELDS = ["kind", "name", "description", "instructions", "model"]

# Required model fields
REQUIRED_MODEL_FIELDS = ["id", "provider", "connection"]

# Agents that participate in the declarative workflow and MUST have outputSchema
# All workflow agents need structured output for proper routing decisions
WORKFLOW_AGENTS = ["orchestrator", "support", "ticketing"]


def get_agent_files() -> list[Path]:
    """Get all agent YAML files."""
    return list(AGENTS_DIR.glob("*.yaml"))


def get_workflow_files() -> list[Path]:
    """Get all workflow YAML files."""
    return list(WORKFLOW_DIR.glob("*.yaml"))


def load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestAgentSchema:
    """Tests for agent YAML schema validation."""

    @pytest.mark.parametrize("agent_file", get_agent_files(), ids=lambda x: x.stem)
    def test_agent_has_required_fields(self, agent_file: Path):
        """Test that all agents have required fields."""
        agent = load_yaml(agent_file)
        
        for field in REQUIRED_AGENT_FIELDS:
            assert field in agent, f"Missing required field '{field}' in {agent_file.name}"

    @pytest.mark.parametrize("agent_file", get_agent_files(), ids=lambda x: x.stem)
    def test_agent_kind_is_valid(self, agent_file: Path):
        """Test that agent kind is valid."""
        agent = load_yaml(agent_file)
        
        valid_kinds = ["Agent", "Prompt"]
        assert agent.get("kind") in valid_kinds, \
            f"Invalid kind '{agent.get('kind')}' in {agent_file.name}. Must be one of {valid_kinds}"

    @pytest.mark.parametrize("agent_file", get_agent_files(), ids=lambda x: x.stem)
    def test_agent_has_name(self, agent_file: Path):
        """Test that agent has a non-empty name."""
        agent = load_yaml(agent_file)
        
        name = agent.get("name")
        assert name is not None, f"Agent name is None in {agent_file.name}"
        assert isinstance(name, str), f"Agent name must be string in {agent_file.name}"
        assert len(name) > 0, f"Agent name is empty in {agent_file.name}"

    @pytest.mark.parametrize("agent_file", get_agent_files(), ids=lambda x: x.stem)
    def test_agent_model_has_required_fields(self, agent_file: Path):
        """Test that model configuration has required fields."""
        agent = load_yaml(agent_file)
        model = agent.get("model", {})
        
        for field in REQUIRED_MODEL_FIELDS:
            assert field in model, \
                f"Missing required model field '{field}' in {agent_file.name}"

    @pytest.mark.parametrize("agent_file", get_agent_files(), ids=lambda x: x.stem)
    def test_agent_model_uses_env_variables(self, agent_file: Path):
        """Test that model uses environment variables for configuration."""
        agent = load_yaml(agent_file)
        model = agent.get("model", {})
        
        # Model ID should reference environment variable
        model_id = model.get("id", "")
        assert model_id.startswith("=Env."), \
            f"Model ID should use environment variable (=Env.MODEL_*) in {agent_file.name}"
        
        # Connection endpoint should reference environment variable
        connection = model.get("connection", {})
        endpoint = connection.get("endpoint", "")
        assert endpoint.startswith("=Env."), \
            f"Connection endpoint should use environment variable in {agent_file.name}"

    @pytest.mark.parametrize("agent_file", get_agent_files(), ids=lambda x: x.stem)
    def test_agent_model_provider_is_valid(self, agent_file: Path):
        """Test that model provider is valid."""
        agent = load_yaml(agent_file)
        model = agent.get("model", {})
        
        valid_providers = ["AzureAIAgentClient", "AzureAIClient", "AzureOpenAIChatClient"]
        provider = model.get("provider")
        assert provider in valid_providers, \
            f"Invalid provider '{provider}' in {agent_file.name}. Must be one of {valid_providers}"


class TestWorkflowAgentOutputSchema:
    """Tests for agents that participate in workflows - they MUST have outputSchema."""

    @pytest.mark.parametrize("agent_name", WORKFLOW_AGENTS)
    def test_workflow_agent_has_output_schema(self, agent_name: str):
        """Test that workflow agents have outputSchema defined."""
        agent_file = AGENTS_DIR / f"{agent_name}.yaml"
        assert agent_file.exists(), f"Agent file not found: {agent_file}"
        
        agent = load_yaml(agent_file)
        assert "outputSchema" in agent, \
            f"Workflow agent '{agent_name}' must have outputSchema for routing decisions"

    @pytest.mark.parametrize("agent_name", WORKFLOW_AGENTS)
    def test_output_schema_has_properties(self, agent_name: str):
        """Test that outputSchema has properties defined."""
        agent_file = AGENTS_DIR / f"{agent_name}.yaml"
        agent = load_yaml(agent_file)
        
        output_schema = agent.get("outputSchema", {})
        properties = output_schema.get("properties", {})
        
        assert properties, \
            f"outputSchema.properties is empty in {agent_name}.yaml"


class TestOrchestratorOutputSchema:
    """Tests specific to Orchestrator agent outputSchema."""

    def test_orchestrator_has_intent_property(self):
        """Test that Orchestrator has Intent property."""
        agent = load_yaml(AGENTS_DIR / "orchestrator.yaml")
        properties = agent.get("outputSchema", {}).get("properties", {})
        
        assert "Intent" in properties, \
            "Orchestrator must have 'Intent' in outputSchema for routing"

    def test_orchestrator_has_intent_classified_property(self):
        """Test that Orchestrator has IntentClassified property."""
        agent = load_yaml(AGENTS_DIR / "orchestrator.yaml")
        properties = agent.get("outputSchema", {}).get("properties", {})
        
        assert "IntentClassified" in properties, \
            "Orchestrator must have 'IntentClassified' in outputSchema for externalLoop"


class TestSupportOutputSchema:
    """Tests specific to Support agent outputSchema."""

    def test_support_has_is_resolved_property(self):
        """Test that Support has IsResolved property."""
        agent = load_yaml(AGENTS_DIR / "support.yaml")
        properties = agent.get("outputSchema", {}).get("properties", {})
        
        assert "IsResolved" in properties, \
            "Support must have 'IsResolved' in outputSchema for workflow routing"

    def test_support_has_needs_ticket_property(self):
        """Test that Support has NeedsTicket property."""
        agent = load_yaml(AGENTS_DIR / "support.yaml")
        properties = agent.get("outputSchema", {}).get("properties", {})
        
        assert "NeedsTicket" in properties, \
            "Support must have 'NeedsTicket' in outputSchema for escalation"


class TestTicketingOutputSchema:
    """Tests specific to Ticketing agent outputSchema."""

    def test_ticketing_has_ticket_created_property(self):
        """Test that Ticketing has TicketCreated property."""
        agent = load_yaml(AGENTS_DIR / "ticketing.yaml")
        properties = agent.get("outputSchema", {}).get("properties", {})
        
        assert "TicketCreated" in properties, \
            "Ticketing must have 'TicketCreated' in outputSchema for workflow completion"


class TestMCPConfiguration:
    """Tests for MCP tool configuration."""

    @pytest.mark.parametrize("agent_file", get_agent_files(), ids=lambda x: x.stem)
    def test_mcp_tools_use_env_for_connection_name(self, agent_file: Path):
        """Test that MCP tools use environment variable for connection name."""
        agent = load_yaml(agent_file)
        tools = agent.get("tools", [])
        
        for tool in tools:
            if tool.get("kind") == "mcp":
                connection = tool.get("connection", {})
                name = connection.get("name", "")
                
                # Should use environment variable, not hardcoded value
                if name and not name.startswith("=Env."):
                    # Allow MSLearnMCP as it's a public service
                    if name != "MSLearnMCP":
                        pytest.fail(
                            f"MCP connection name should use environment variable "
                            f"(=Env.MCP_CONNECTION_NAME) in {agent_file.name}, "
                            f"got '{name}'"
                        )


class TestWorkflowSchema:
    """Tests for workflow YAML schema validation."""

    @pytest.mark.parametrize("workflow_file", get_workflow_files(), ids=lambda x: x.stem)
    def test_workflow_has_required_fields(self, workflow_file: Path):
        """Test that workflows have required fields."""
        workflow = load_yaml(workflow_file)
        
        assert workflow.get("kind") == "Workflow", \
            f"Workflow kind must be 'Workflow' in {workflow_file.name}"
        assert "name" in workflow, \
            f"Missing 'name' in {workflow_file.name}"
        assert "trigger" in workflow, \
            f"Missing 'trigger' in {workflow_file.name}"

    @pytest.mark.parametrize("workflow_file", get_workflow_files(), ids=lambda x: x.stem)
    def test_workflow_trigger_has_actions(self, workflow_file: Path):
        """Test that workflow trigger has actions defined."""
        workflow = load_yaml(workflow_file)
        trigger = workflow.get("trigger", {})
        
        assert "actions" in trigger, \
            f"Trigger must have 'actions' in {workflow_file.name}"
        assert len(trigger.get("actions", [])) > 0, \
            f"Trigger actions cannot be empty in {workflow_file.name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
