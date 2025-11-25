from typing import Optional
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.events import Event

from backend.config.logging import get_logger
from backend.utils.adk_message_utils import format_content

logger = get_logger(__name__)


class MessageValidationPlugin(BasePlugin):
    """A custom plugin that validates messages."""

    def __init__(self) -> None:
        super().__init__(name="message_validation")
        logger.info(f"[MessageValidationPlugin] {self.name} plugin initialized")

    def is_empty_response(self, llm_response: LlmResponse) -> bool:
        return llm_response.content is None or \
            (len(llm_response.content.parts) == 1 and \
             (llm_response.content.parts[0].text is None or len(llm_response.content.parts[0].text) == 0))

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Count agent runs."""
        logger.debug(f"[MessageValidationPlugin] Before agent {agent.name} callback")

    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Count agent runs."""
        logger.debug(f"[MessageValidationPlugin] After agent {agent.name} callback")

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        logger.debug("[MessageValidationPlugin] Before model callback")
        logger.debug(f"   User Request: {format_content(llm_request.contents[-1])}")
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        logger.debug("[MessageValidationPlugin] After model callback")
        logger.debug(f"   LLM Response: {format_content(llm_response.content)}")
        if llm_response.content is None or self.is_empty_response(llm_response):
            logger.info("   LLM Response is empty")
            return None
        return llm_response

    async def on_event_callback(
        self, *, invocation_context: InvocationContext, event: Event
    ) -> Optional[Event]:
        """Log events yielded from the runner."""
        logger.debug(f"📢 EVENT YIELDED")
        logger.debug(f"   Event ID: {event.id}")
        logger.debug(f"   Author: {event.author}")
        logger.debug(f"   Content: {format_content(event.content)}")
        logger.debug(f"   Final Response: {event.is_final_response()}")

        if event.content and event.content.parts:
            if event.get_function_calls():
                func_calls = [fc.name for fc in event.get_function_calls()]
                logger.debug(f"   Function Calls: {func_calls}")

            elif event.get_function_responses():
                func_responses = [fr.name for fr in event.get_function_responses()]
                logger.debug(f"   Function Responses: {func_responses}")

            elif event.long_running_tool_ids:
                logger.debug(f"   Long Running Tools: {list(event.long_running_tool_ids)}")

            elif event.content.parts[0].text:
                if event.partial:
                    logger.debug("   Type: Streaming Text Chunk")
                else:
                    logger.debug("   Type: Complete Text Message")
            else:
                logger.debug("   Type: Non-text Message")
        return None
