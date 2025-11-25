# src/endpoint.py

"""FastAPI endpoint for ADK middleware."""


from ag_ui.core import RunAgentInput, BaseEvent
from ag_ui.core.events import EventType
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..config.logging import get_logger
from .adk_plugins import get_default_plugins
from .ag_ui_wrapper import AgentFactory

logger = get_logger(__name__)


class AdkFastAPIEndpoint:
    """ADK middleware endpoint."""

    def __init__(self, agent_dir: str):
        self.agent_factory = AgentFactory(agent_dir, plugins=get_default_plugins())

    def _is_filtered(self, event: BaseEvent) -> bool:
        """Filter out events that are not needed for the frontend.

        Args:
            event: Event to filter

        Returns:
            True if the event should be filtered, False otherwise
        """
        if event.type in (EventType.TEXT_MESSAGE_CHUNK, EventType.TEXT_MESSAGE_CONTENT, EventType.THINKING_TEXT_MESSAGE_CONTENT):
            if event.delta == '':
                return True
        return False

    def get_copilotkit_endpoint_router(self):
        """Add ADK middleware endpoint to FastAPI app.

        Args:
            api_router: FastAPI application parent api router
            path: API endpoint path
        """

        adk_router = APIRouter(prefix="/adk")

        @adk_router.post("/copilotkit/{agent_name}")
        async def run(agent_name: str, input_data: RunAgentInput, request: Request):
            """ADK middleware endpoint.

            Args:
                agent_name: Name of the agent to run (from path parameter)
                input_data: Agent input data
                request: HTTP request object
            """

            logger.info(f"Input data: {input_data}")

            # Get the accept header from the request
            accept_header = request.headers.get("accept")

            logger.info(f"🚀 Running agent: {agent_name}")

            agent = await self.agent_factory.create_agent(agent_name)

            # Create an event encoder to properly format SSE events
            encoder = EventEncoder(accept=accept_header)

            async def event_generator():
                """Generate events from ADK agent."""
                try:
                    async for event in agent.run(input_data):
                        try:
                            logger.info(f"Event: {event.model_dump_json()}")
                            encoded = encoder.encode(event)
                            logger.debug(f"Encoded event: {encoded}")
                            yield encoded
                        except Exception as encoding_error:
                            # Handle encoding-specific errors
                            logger.error(
                                f"❌ Event encoding error: {encoding_error}",
                                exc_info=True,
                            )
                            # Create a RunErrorEvent for encoding failures
                            from ag_ui.core import EventType, RunErrorEvent

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
                        from ag_ui.core import EventType, RunErrorEvent

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
