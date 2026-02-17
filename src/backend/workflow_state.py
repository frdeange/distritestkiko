# =============================================================================
# DistriPartner Platform - Workflow State StoreItem
# =============================================================================
# Persists workflow state (pending_request_id) in the M365 Agents SDK
# TurnState / CosmosDB storage between conversation turns.
# =============================================================================

from typing import Optional

from microsoft_agents.hosting.core import StoreItem


class WorkflowStateItem(StoreItem):
    """Stores workflow state between conversation turns."""

    def __init__(
        self,
        pending_request_id: Optional[str] = None,
        user_identity: Optional[str] = None,
    ):
        self.pending_request_id = pending_request_id
        # Pre-built system context block from the first message
        self.user_identity = user_identity

    def store_item_to_json(self) -> dict:
        return {
            "pending_request_id": self.pending_request_id,
            "user_identity": self.user_identity,
        }

    @staticmethod
    def from_json_to_store_item(json_data: dict) -> "WorkflowStateItem":
        return WorkflowStateItem(
            pending_request_id=json_data.get("pending_request_id"),
            user_identity=json_data.get("user_identity"),
        )
