from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.plugins.base_plugin import BasePlugin

from backend.config.logging import get_logger

logger = get_logger(__name__)

class MessageValidationPlugin(BasePlugin):
  """A custom plugin that validates messages."""

  def __init__(self) -> None:
    super().__init__(name="message_validation")
    logger.info(f"[MessageValidationPlugin] {self.name} plugin initialized <<<<<<")

  async def after_agent_callback(
      self, *, agent: BaseAgent, callback_context: CallbackContext
  ) -> None:
    """Count agent runs."""
    logger.info(f"[MessageValidationPlugin] After agent callback")