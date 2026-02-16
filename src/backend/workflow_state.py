# =============================================================================
# DistriPartner Platform - Workflow State StoreItem
# =============================================================================
# Persists workflow state (pending_request_id) in the M365 Agents SDK
# TurnState / CosmosDB storage between conversation turns.
# =============================================================================

from typing import Optional

from microsoft_agents.hosting.core import StoreItem


class WorkflowStateItem(StoreItem):
    """Stores the workflow's pending request ID between conversation turns."""

    def __init__(
        self,
        pending_request_id: Optional[str] = None,
    ):
        self.pending_request_id = pending_request_id

    def store_item_to_json(self) -> dict:
        return {
            "pending_request_id": self.pending_request_id,
        }

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "WorkflowStateItem":
        return WorkflowStateItem(
            pending_request_id=json_data.get("pending_request_id"),
        )
