# src/endpoint.py

"""FastAPI endpoint for ADK middleware."""

import os
import click
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from starlette.types import Lifespan
from watchdog.observers import Observer
from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui_adk import ADKAgent
from google.adk.cli.adk_web_server import AdkWebServer
from google.adk.cli.service_registry import get_service_registry
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk.evaluation.local_eval_set_results_manager import LocalEvalSetResultsManager
from google.adk.evaluation.local_eval_sets_manager import LocalEvalSetsManager
from google.adk.cli.utils.agent_loader import AgentLoader
from google.adk.cli.utils import envs
from google.adk.cli.utils import evals
from google.adk.cli.utils.agent_change_handler import AgentChangeEventHandler

import logging

logger = logging.getLogger(__name__)


class AdkFastAPIEndpoint:
    """ADK middleware endpoint."""

    def __init__(self):
        self.adk_web_server = None
        self.extra_fast_api_args = {}

    def _build_adk_agent(self, agent_name: str) -> ADKAgent:
        """构建ADK Agent实例"""
        agent = self.adk_web_server.agent_loader.load_agent(agent_name)

        # 统一的用户 ID 提取器
        def extract_user_id_from_forwarded_props(input: RunAgentInput) -> str:
            """
            从 AG-UI 协议的 forwarded_props 中提取 user_id

            这是全局统一的用户身份提取逻辑，由 AG-UI Router 注入。
            """
            logger.info(
                f"🔍 ADK Agent: Extracting user_id for thread {input.thread_id}"
            )
            logger.info(
                f"🔍 ADK Agent: forwarded_props type: {type(input.forwarded_props)}"
            )
            logger.info(
                f"🔍 ADK Agent: forwarded_props content: {input.forwarded_props}"
            )

            if isinstance(input.forwarded_props, dict):
                user_identity = input.forwarded_props.get("_user_identity", {})
                logger.info(f"🔍 ADK Agent: user_identity extracted: {user_identity}")

                if user_id := user_identity.get("user_id"):
                    logger.info(
                        f"✅ ADK Agent: Successfully extracted user_id from forwarded_props: {user_id}"
                    )
                    return user_id
                else:
                    logger.warning(
                        f"❌ ADK Agent: No user_id found in user_identity: {user_identity}"
                    )

            # Fallback：不应该走到这里
            # 如果走到这里，说明 AG-UI Router 没有正确注入 user_identity
            fallback_id = f"thread_user_{input.thread_id}"
            logger.error(
                f"❌ ADK Agent: No user_identity in forwarded_props for thread {input.thread_id}, "
                f"falling back to {fallback_id}. "
                f"This should NOT happen in normal flow."
            )
            return fallback_id

        return ADKAgent(
            adk_agent=agent,
            app_name=agent_name,
            user_id_extractor=extract_user_id_from_forwarded_props,
            session_service=self.adk_web_server.session_service,
            artifact_service=self.adk_web_server.artifact_service,
            memory_service=self.adk_web_server.memory_service,
            credential_service=self.adk_web_server.credential_service,
            use_in_memory_services=False,
        )

    def get_copilotkit_endpoint_router(self):
        """Add ADK middleware endpoint to FastAPI app.

        Args:
            api_router: FastAPI application parent api router
            path: API endpoint path
        """

        adk_router = APIRouter(prefix="/adk")

        @adk_router.post("/copilotkit")
        async def run(input_data: RunAgentInput, request: Request):
            """ADK middleware endpoint."""

            # Get the accept header from the request
            accept_header = request.headers.get("accept")
            agent_name = "copilotkit".lstrip("/")

            agent = self._build_adk_agent(agent_name)

            # Create an event encoder to properly format SSE events
            encoder = EventEncoder(accept=accept_header)

            async def event_generator():
                """Generate events from ADK agent."""
                try:
                    async for event in agent.run(input_data):
                        try:
                            encoded = encoder.encode(event)
                            logger.debug(f"HTTP Response: {encoded}")
                            yield encoded
                        except Exception as encoding_error:
                            # Handle encoding-specific errors
                            logger.error(
                                f"❌ Event encoding error: {encoding_error}",
                                exc_info=True,
                            )
                            # Create a RunErrorEvent for encoding failures
                            from ag_ui.core import RunErrorEvent, EventType

                            error_event = RunErrorEvent(
                                type=EventType.RUN_ERROR,
                                message=f"Event encoding failed: {str(encoding_error)}",
                                code="ENCODING_ERROR",
                            )
                            try:
                                error_encoded = encoder.encode(error_event)
                                yield error_encoded
                            except Exception:
                                # If we can't even encode the error event, yield a basic SSE error
                                logger.error(
                                    "Failed to encode error event, yielding basic SSE error"
                                )
                                yield 'event: error\ndata: {"error": "Event encoding failed"}\n\n'
                            break  # Stop the stream after an encoding error
                except Exception as agent_error:
                    # Handle errors from ADKAgent.run() itself
                    logger.error(f"❌ ADKAgent error: {agent_error}", exc_info=True)
                    # ADKAgent should have yielded a RunErrorEvent, but if something went wrong
                    # in the async generator itself, we need to handle it
                    try:
                        from ag_ui.core import RunErrorEvent, EventType

                        error_event = RunErrorEvent(
                            type=EventType.RUN_ERROR,
                            message=f"Agent execution failed: {str(agent_error)}",
                            code="AGENT_ERROR",
                        )
                        error_encoded = encoder.encode(error_event)
                        yield error_encoded
                    except Exception:
                        # If we can't encode the error event, yield a basic SSE error
                        logger.error(
                            "Failed to encode agent error event, yielding basic SSE error"
                        )
                        yield 'event: error\ndata: {"error": "Agent execution failed"}\n\n'

            return StreamingResponse(
                event_generator(), media_type=encoder.get_content_type()
            )
        
        return adk_router


    def create_adk_web_server(
        self,
        *,
        agents_dir: str,
        session_service_uri: Optional[str] = None,
        session_db_kwargs: Optional[Mapping[str, Any]] = None,
        artifact_service_uri: Optional[str] = None,
        memory_service_uri: Optional[str] = None,
        eval_storage_uri: Optional[str] = None,
        url_prefix: Optional[str] = None,
        extra_plugins: Optional[list[str]] = None,
        logo_text: Optional[str] = None,
        logo_image_url: Optional[str] = None,
    ) -> None:
        # Set up eval managers.
        if eval_storage_uri:
            gcs_eval_managers = evals.create_gcs_eval_managers_from_uri(eval_storage_uri)
            eval_sets_manager = gcs_eval_managers.eval_sets_manager
            eval_set_results_manager = gcs_eval_managers.eval_set_results_manager
        else:
            eval_sets_manager = LocalEvalSetsManager(agents_dir=agents_dir)
            eval_set_results_manager = LocalEvalSetResultsManager(agents_dir=agents_dir)

        service_registry = get_service_registry()

        # Build the Memory service
        if memory_service_uri:
            memory_service = service_registry.create_memory_service(
                memory_service_uri, agents_dir=agents_dir
            )
            if not memory_service:
                raise click.ClickException(
                    "Unsupported memory service URI: %s" % memory_service_uri
                )
        else:
            memory_service = InMemoryMemoryService()

        # Build the Session service
        if session_service_uri:
            session_kwargs = session_db_kwargs or {}
            session_service = service_registry.create_session_service(
                session_service_uri, agents_dir=agents_dir, **session_kwargs
            )
            if not session_service:
                # Fallback to DatabaseSessionService if the service registry doesn't
                # support the session service URI scheme.
                from google.adk.sessions.database_session_service import DatabaseSessionService

                session_service = DatabaseSessionService(
                    db_url=session_service_uri, **session_kwargs
                )
        else:
            session_service = InMemorySessionService()

        # Build the Artifact service
        if artifact_service_uri:
            artifact_service = service_registry.create_artifact_service(
                artifact_service_uri, agents_dir=agents_dir
            )
            if not artifact_service:
                raise click.ClickException(
                    "Unsupported artifact service URI: %s" % artifact_service_uri
                )
        else:
            artifact_service = InMemoryArtifactService()

        # Build  the Credential service
        credential_service = InMemoryCredentialService()

        # initialize Agent Loader
        agent_loader = AgentLoader(agents_dir)

        self.adk_web_server = AdkWebServer(
            agent_loader=agent_loader,
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,
            credential_service=credential_service,
            eval_sets_manager=eval_sets_manager,
            eval_set_results_manager=eval_set_results_manager,
            agents_dir=agents_dir,
            extra_plugins=extra_plugins,
            logo_text=logo_text,
            logo_image_url=logo_image_url,
            url_prefix=url_prefix,
        )

