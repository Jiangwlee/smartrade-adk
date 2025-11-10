# backend/api/ag_ui_wrapper.py

"""
SmartradeADKAgent - Fixed ADKAgent wrapper that properly marks ToolMessages as processed

Problem:
ag_ui_adk.ADKAgent does not call mark_messages_processed after handling ToolMessages,
causing processed ToolMessages to be treated as new messages repeatedly,
leading to duplicate confirmation responses from the LLM.

Solution:
Inherit from ADKAgent and override the run() method to add ToolMessage marking logic.
"""

from typing import AsyncGenerator, List, Any
from ag_ui.core import RunAgentInput, BaseEvent
from ag_ui_adk import ADKAgent
from backend.config.logging import get_logger

logger = get_logger(__name__)


class SmartradeADKAgent(ADKAgent):
    """Fixed ADKAgent that properly marks ToolMessages as processed

    This class inherits from ag_ui_adk.ADKAgent and fixes:
    1. ToolMessages not being marked as processed after handling
    2. Old ToolMessages being processed repeatedly

    Usage:
        agent = SmartradeADKAgent(
            adk_agent=my_adk_agent,
            app_name="my_app",
            ...
        )
    """

    async def run(self, input: RunAgentInput) -> AsyncGenerator[BaseEvent, None]:
        """Override run method to add ToolMessage marking logic

        Args:
            input: The AG-UI run input

        Yields:
            AG-UI protocol events
        """
        unseen_messages = await self._get_unseen_messages(input)

        if not unseen_messages:
            # No unseen messages - fall through to normal execution handling
            async for event in self._start_new_execution(input):
                yield event
            return

        index = 0
        total_unseen = len(unseen_messages)
        app_name = self._get_app_name(input)
        skip_tool_message_batch = False

        while index < total_unseen:
            current = unseen_messages[index]
            role = getattr(current, "role", None)

            if role == "tool":
                # FIX: Collect ToolMessage IDs and check if they have pending tool calls
                tool_batch: List[Any] = []
                tool_message_ids: List[str] = []
                has_pending_tools = False

                while index < total_unseen and getattr(unseen_messages[index], "role", None) == "tool":
                    msg = unseen_messages[index]
                    tool_batch.append(msg)

                    msg_id = getattr(msg, "id", None)
                    if msg_id:
                        tool_message_ids.append(msg_id)

                    index += 1

                # Check if any of these tool messages correspond to pending tool calls
                if await self._has_pending_tool_calls(input.thread_id):
                    has_pending_tools = True

                # FIX: Only process tool results if they correspond to pending tool calls
                # Otherwise, they are old messages from history that have already been processed
                if has_pending_tools:
                    logger.info(
                        f"🔧 [SmartradeADKAgent] Processing {len(tool_batch)} pending tool results"
                    )
                    async for event in self._handle_tool_result_submission(
                        input,
                        tool_messages=tool_batch,
                        include_message_batch=not skip_tool_message_batch,
                    ):
                        yield event
                else:
                    # These are old ToolMessages from history, just mark them as processed
                    logger.info(
                        f"🔧 [SmartradeADKAgent] Skipping {len(tool_batch)} old ToolMessages (no pending tool calls), marking as processed: {tool_message_ids}"
                    )
                    if tool_message_ids:
                        self._session_manager.mark_messages_processed(
                            app_name,
                            input.thread_id,
                            tool_message_ids,
                        )

                skip_tool_message_batch = False
            else:
                # Handle non-tool messages (original logic unchanged)
                message_batch: List[Any] = []
                assistant_message_ids: List[str] = []

                while index < total_unseen and getattr(unseen_messages[index], "role", None) != "tool":
                    candidate = unseen_messages[index]
                    candidate_role = getattr(candidate, "role", None)

                    if candidate_role == "assistant":
                        message_id = getattr(candidate, "id", None)
                        if message_id:
                            assistant_message_ids.append(message_id)
                    else:
                        message_batch.append(candidate)

                    index += 1

                if assistant_message_ids:
                    self._session_manager.mark_messages_processed(
                        app_name,
                        input.thread_id,
                        assistant_message_ids,
                    )

                if not message_batch:
                    if assistant_message_ids:
                        skip_tool_message_batch = True
                    continue
                else:
                    skip_tool_message_batch = False

                async for event in self._start_new_execution(input, message_batch=message_batch):
                    yield event
