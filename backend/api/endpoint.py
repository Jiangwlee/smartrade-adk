# src/endpoint.py

"""FastAPI endpoint for ADK middleware."""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui_adk import ADKAgent
from google.adk.cli.adk_web_server import AdkWebServer

import logging
logger = logging.getLogger(__name__)

class AdkFastAPIEndpoint:
    """ADK middleware endpoint."""
    def __init__(self, agents_dir: str):
        self.adk_web_server = AdkWebServer(agents_dir=agents_dir)

    
    def _build_adk_agent(self, agent_name: str) -> ADKAgent:
        """构建ADK Agent实例"""
        agent = self.adk_web_server.agent_loader.load_agent(agent_name)

        # 统一的用户 ID 提取器
        def extract_user_id_from_forwarded_props(input: RunAgentInput) -> str:
            """
            从 AG-UI 协议的 forwarded_props 中提取 user_id

            这是全局统一的用户身份提取逻辑，由 AG-UI Router 注入。
            """
            logger.info(f"🔍 ADK Agent: Extracting user_id for thread {input.thread_id}")
            logger.info(f"🔍 ADK Agent: forwarded_props type: {type(input.forwarded_props)}")
            logger.info(f"🔍 ADK Agent: forwarded_props content: {input.forwarded_props}")

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

    def add_adk_fastapi_endpoint(self, app: FastAPI, path: str = "/"):
        """Add ADK middleware endpoint to FastAPI app.
        
        Args:
            app: FastAPI application instance
            path: API endpoint path
        """
        
        @app.post(path)
        async def run(input_data: RunAgentInput, request: Request):
            """ADK middleware endpoint."""
            
            # Get the accept header from the request
            accept_header = request.headers.get("accept")
            agent_name = path.lstrip('/')

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
                            logger.error(f"❌ Event encoding error: {encoding_error}", exc_info=True)
                            # Create a RunErrorEvent for encoding failures
                            from ag_ui.core import RunErrorEvent, EventType
                            error_event = RunErrorEvent(
                                type=EventType.RUN_ERROR,
                                message=f"Event encoding failed: {str(encoding_error)}",
                                code="ENCODING_ERROR"
                            )
                            try:
                                error_encoded = encoder.encode(error_event)
                                yield error_encoded
                            except Exception:
                                # If we can't even encode the error event, yield a basic SSE error
                                logger.error("Failed to encode error event, yielding basic SSE error")
                                yield "event: error\ndata: {\"error\": \"Event encoding failed\"}\n\n"
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
                            code="AGENT_ERROR"
                        )
                        error_encoded = encoder.encode(error_event)
                        yield error_encoded
                    except Exception:
                        # If we can't encode the error event, yield a basic SSE error
                        logger.error("Failed to encode agent error event, yielding basic SSE error")
                        yield "event: error\ndata: {\"error\": \"Agent execution failed\"}\n\n"
            
            return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
