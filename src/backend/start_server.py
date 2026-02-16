# =============================================================================
# DistriPartner Platform - aiohttp Server
# =============================================================================
# HTTP server following the M365 Agents SDK pattern.
# Handles incoming Teams messages via /api/messages endpoint.
# =============================================================================

import logging
from os import environ

from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration
from microsoft_agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)
from aiohttp.web import Request, Response, Application, run_app, json_response

from .config import PORT

logger = logging.getLogger(__name__)


def start_server(
    agent_application: AgentApplication,
    auth_configuration: AgentAuthConfiguration,
):
    """
    Start the aiohttp server for the Teams bot.

    Args:
        agent_application: Configured M365 AgentApplication instance
        auth_configuration: Authentication configuration from MsalConnectionManager
    """

    async def entry_point(req: Request) -> Response:
        """POST /api/messages - processes incoming Teams activities."""
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        return await start_agent_process(req, agent, adapter)

    async def health_check(req: Request) -> Response:
        """GET /api/health - health check for Azure Container Apps."""
        return json_response({"status": "healthy", "service": "distripartner-bot"})

    async def on_startup(app: Application):
        """Start background tasks when server starts."""
        from .bot import WORKFLOW_MANAGER

        WORKFLOW_MANAGER.start_cleanup()
        logger.info("Workflow cleanup task started")

    async def on_shutdown(app: Application):
        """Clean up when server stops."""
        from .bot import WORKFLOW_MANAGER

        WORKFLOW_MANAGER.stop_cleanup()
        logger.info("Workflow cleanup task stopped")

    # Create aiohttp application
    APP = Application(middlewares=[jwt_authorization_middleware])
    APP.router.add_post("/api/messages", entry_point)
    APP.router.add_get("/api/health", health_check)

    APP["agent_configuration"] = auth_configuration
    APP["agent_app"] = agent_application
    APP["adapter"] = agent_application.adapter

    APP.on_startup.append(on_startup)
    APP.on_shutdown.append(on_shutdown)

    logger.info("Starting DistriPartner bot on 0.0.0.0:%s", PORT)

    try:
        run_app(APP, host="0.0.0.0", port=PORT)
    except Exception as error:
        logger.exception("Server error")
        raise error
