# =============================================================================
# DistriPartner Platform - Workflow Manager
# =============================================================================
# Manages workflow instances per conversation. Each Teams conversation gets
# its own workflow instance that persists in memory between message turns.
#
# The workflow object must stay alive between HTTP requests because
# workflow.run(responses={id: response}) resumes from where it left off.
# =============================================================================

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from azure.identity import DefaultAzureCredential

from agent_framework.declarative import (
    AgentExternalInputRequest,
    AgentExternalInputResponse,
)

import sys
from pathlib import Path

# Add src to path so workflows module is importable
_src_dir = str(Path(__file__).parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from workflows.declarative import create_declarative_workflow

from .config import SESSION_TTL_SECONDS

logger = logging.getLogger(__name__)


@dataclass
class WorkflowEvent:
    """Event emitted by the workflow manager to the bot handler."""

    type: str  # "text", "activity", "waiting_for_input", "completed"
    text: str = ""
    agent_name: str = ""
    pending_request_id: Optional[str] = None


@dataclass
class WorkflowSession:
    """A per-conversation workflow instance."""

    workflow: object  # The agent-framework workflow object
    pending_request_id: Optional[str] = None
    last_activity: float = field(default_factory=time.time)


class WorkflowManager:
    """
    Manages workflow lifecycle per conversation.

    Each conversation gets its own workflow instance that persists in memory.
    Sessions are cleaned up after SESSION_TTL_SECONDS of inactivity.
    """

    def __init__(self):
        self._sessions: dict[str, WorkflowSession] = {}
        # Use the User-Assigned MSI client ID so DefaultAzureCredential picks the
        # correct identity (instead of the Container App's System-Assigned one)
        msi_client_id = os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID")
        self._credential = DefaultAzureCredential(
            managed_identity_client_id=msi_client_id
        )
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup(self):
        """Start the periodic cleanup task for stale sessions."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    def stop_cleanup(self):
        """Stop the periodic cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    def _get_or_create_session(self, conversation_id: str) -> WorkflowSession:
        """Get an existing session or create a new one."""
        if conversation_id not in self._sessions:
            logger.info("Creating new workflow session for %s", conversation_id)
            workflow = create_declarative_workflow(self._credential)
            self._sessions[conversation_id] = WorkflowSession(workflow=workflow)
        session = self._sessions[conversation_id]
        session.last_activity = time.time()
        return session

    def reset_session(self, conversation_id: str):
        """Remove a conversation's workflow session."""
        if conversation_id in self._sessions:
            del self._sessions[conversation_id]
            logger.info("Reset workflow session for %s", conversation_id)

    async def process_message(
        self,
        conversation_id: str,
        user_input: str,
        pending_request_id: Optional[str] = None,
    ) -> AsyncGenerator[WorkflowEvent, None]:
        """
        Process a user message through the workflow.

        Args:
            conversation_id: Teams conversation ID
            user_input: The user's message text
            pending_request_id: If resuming a multi-turn conversation

        Yields:
            WorkflowEvent objects for the bot handler to send to Teams
        """
        session = self._get_or_create_session(conversation_id)

        # Start or resume the workflow
        if pending_request_id:
            logger.info("Resuming workflow for %s", conversation_id)
            response = AgentExternalInputResponse(user_input=user_input)
            stream = session.workflow.run(
                stream=True, responses={pending_request_id: response}
            )
        else:
            logger.info("Starting workflow for %s", conversation_id)
            stream = session.workflow.run(user_input, stream=True)

        accumulated_text = ""
        new_pending_id = None
        last_agent_name = ""

        async for event in stream:
            if event.type == "output":
                source_id = event.executor_id or ""

                if "log_" in source_id.lower():
                    # Flush accumulated text first
                    if accumulated_text:
                        user_text = _extract_response_text(accumulated_text)
                        if user_text:
                            yield WorkflowEvent(
                                type="text",
                                text=user_text,
                                agent_name=last_agent_name,
                            )
                        accumulated_text = ""

                    # Activity/log message
                    yield WorkflowEvent(
                        type="activity",
                        text=str(event.data) if event.data else "",
                    )
                else:
                    # Accumulate streaming text
                    text = str(event.data) if event.data else ""
                    accumulated_text += text

            elif event.type == "request_info" and isinstance(
                event.data, AgentExternalInputRequest
            ):
                request = event.data
                last_agent_name = request.agent_name

                # The agent's structured response contains the user-facing text
                if request.agent_response:
                    user_text = _extract_response_text(request.agent_response)
                    if user_text:
                        yield WorkflowEvent(
                            type="text",
                            text=user_text,
                            agent_name=last_agent_name,
                        )

                accumulated_text = ""
                new_pending_id = event.request_id

        # Flush remaining accumulated text
        if accumulated_text:
            user_text = _extract_response_text(accumulated_text)
            if user_text:
                yield WorkflowEvent(
                    type="text", text=user_text, agent_name=last_agent_name
                )

        # Emit final status event
        if new_pending_id:
            session.pending_request_id = new_pending_id
            yield WorkflowEvent(
                type="waiting_for_input",
                pending_request_id=new_pending_id,
                agent_name=last_agent_name,
            )
        else:
            # Workflow completed - clean up session
            self.reset_session(conversation_id)
            yield WorkflowEvent(type="completed")

    async def _cleanup_loop(self):
        """Periodically remove stale sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                now = time.time()
                stale = [
                    cid
                    for cid, session in self._sessions.items()
                    if now - session.last_activity > SESSION_TTL_SECONDS
                ]
                for cid in stale:
                    logger.info("Cleaning up stale session: %s", cid)
                    del self._sessions[cid]
                if stale:
                    logger.info("Cleaned up %d stale sessions", len(stale))
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in cleanup loop")


def _extract_response_text(raw: str) -> str:
    """
    Extract user-facing Response field(s) from agent output.

    Handles:
    - Single JSON object with a Response field
    - Multiple JSON objects concatenated (streaming accumulation)
    - Mixed JSON + plain text segments

    For multiple JSON objects, returns only the LAST Response (the most
    up-to-date status) plus any trailing non-JSON text.
    """
    stripped = raw.strip()
    if not stripped:
        return ""

    # Fast path: single valid JSON
    try:
        parsed = json.loads(stripped)
        response = parsed.get("Response", "") or parsed.get("response", "")
        if response:
            return response
        logger.debug("No Response field in JSON, suppressing: %s", stripped[:200])
        return ""
    except (json.JSONDecodeError, TypeError):
        pass

    # Slow path: multiple JSON objects and/or plain text segments
    json_responses: list[str] = []
    text_segments: list[str] = []
    pos = 0

    while pos < len(stripped):
        # Skip whitespace
        while pos < len(stripped) and stripped[pos] in " \t\n\r":
            pos += 1
        if pos >= len(stripped):
            break

        if stripped[pos] == "{":
            # Find the matching closing brace
            depth = 0
            in_str = False
            esc = False
            end = pos
            for i in range(pos, len(stripped)):
                c = stripped[i]
                if esc:
                    esc = False
                    continue
                if c == "\\" and in_str:
                    esc = True
                    continue
                if c == '"' and not esc:
                    in_str = not in_str
                    continue
                if not in_str:
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            end = i
                            break

            json_str = stripped[pos : end + 1]
            pos = end + 1
            try:
                obj = json.loads(json_str)
                resp = obj.get("Response", "") or obj.get("response", "")
                if resp:
                    json_responses.append(resp)
            except (json.JSONDecodeError, TypeError):
                pass  # skip malformed JSON
        else:
            # Non-JSON text: read until next '{' or end
            next_brace = stripped.find("{", pos)
            if next_brace == -1:
                segment = stripped[pos:].strip()
                if segment:
                    text_segments.append(segment)
                break
            else:
                segment = stripped[pos:next_brace].strip()
                if segment:
                    text_segments.append(segment)
                pos = next_brace

    # Build result: last JSON Response (final status) + non-JSON text
    parts: list[str] = []
    if json_responses:
        parts.append(json_responses[-1])
    parts.extend(text_segments)
    return "\n\n".join(parts) if parts else ""
