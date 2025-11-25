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
import os
from typing import Optional, Callable, Any, AsyncGenerator, List

from ag_ui.core import (
    RunAgentInput, BaseEvent,
)

from google.adk import Runner
from google.adk.agents import BaseAgent, RunConfig as ADKRunConfig
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.adk.artifacts import BaseArtifactService, InMemoryArtifactService
from google.adk.memory import BaseMemoryService, InMemoryMemoryService
from google.adk.auth.credential_service.base_credential_service import BaseCredentialService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk.apps import App
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.cli.utils.agent_loader import AgentLoader
from google.adk.cli.utils import envs
from ag_ui_adk import ADKAgent
from backend.config.logging import get_logger

logger = get_logger(__name__)

class AgentFactory:
    def __init__(
            self,  
            agents_dir: str, 
            plugins: Optional[List[BasePlugin]] = [],
            # ADK Services
            session_service: Optional[BaseSessionService] = None,
            artifact_service: Optional[BaseArtifactService] = None,
            memory_service: Optional[BaseMemoryService] = None,
            credential_service: Optional[BaseCredentialService] = None
        ):
        self.agents_dir = agents_dir
        self.agent_loader = AgentLoader(agents_dir)
        self.plugins = plugins
        self.session_service = session_service or InMemorySessionService()
        self.artifact_service = artifact_service or InMemoryArtifactService()
        self.memory_service = memory_service or InMemoryMemoryService()
        self.credential_service = credential_service or InMemoryCredentialService()
        self.agents_dict = {}
    
    async def create_agent(self, app_name: str) -> ADKAgent:
        """Returns the cached runner for the given app."""
        # Create new agent
        envs.load_dotenv_for_agent(os.path.basename(app_name), self.agents_dir)
        agent_or_app = self.agent_loader.load_agent(app_name)

        if isinstance(agent_or_app, BaseAgent):
            agentic_app = App(
                name=app_name,
                root_agent=agent_or_app,
                plugins=self.plugins,
            )
        else:
            # Combine existing plugins with extra plugins
            agent_or_app.plugins = agent_or_app.plugins + self.plugins
            agentic_app = agent_or_app

        agent = SmartradeADKAgent(
            adk_agent=agentic_app.root_agent,
            app=agentic_app,
            app_name=app_name,
            session_service=self.session_service,
            artifact_service=self.artifact_service,
            memory_service=self.memory_service,
            credential_service=self.credential_service,
        )
        self.agents_dict[app_name] = agent
        return agent

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
    def __init__(
        self,
        # ADK Agent instance
        adk_agent: BaseAgent,

        # Plugins
        plugins: Optional[List[BasePlugin]] = None,
        
        # App identification
        app: Optional[App] = None,
        app_name: Optional[str] = None,
        session_timeout_seconds: Optional[int] = 1200,
        app_name_extractor: Optional[Callable[[RunAgentInput], str]] = None,
        
        # User identification
        user_id: Optional[str] = None,
        user_id_extractor: Optional[Callable[[RunAgentInput], str]] = None,
        
        # ADK Services
        session_service: Optional[BaseSessionService] = None,
        artifact_service: Optional[BaseArtifactService] = None,
        memory_service: Optional[BaseMemoryService] = None,
        credential_service: Optional[BaseCredentialService] = None,
        
        # Configuration
        run_config_factory: Optional[Callable[[RunAgentInput], ADKRunConfig]] = None,
        use_in_memory_services: bool = True,
        
        # Tool configuration
        execution_timeout_seconds: int = 600,  # 10 minutes
        tool_timeout_seconds: int = 300,  # 5 minutes
        max_concurrent_executions: int = 10,
        
        # Session cleanup configuration
        cleanup_interval_seconds: int = 300  # 5 minutes default
    ):
        super().__init__(
            adk_agent=adk_agent,
            app_name=app_name,
            session_timeout_seconds=session_timeout_seconds,
            app_name_extractor=app_name_extractor,
            user_id=user_id,
            user_id_extractor=user_id_extractor,
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,
            credential_service=credential_service,
            run_config_factory=run_config_factory,
            use_in_memory_services=use_in_memory_services,
            execution_timeout_seconds=execution_timeout_seconds,
            tool_timeout_seconds=tool_timeout_seconds,
            max_concurrent_executions=max_concurrent_executions,
            cleanup_interval_seconds=cleanup_interval_seconds,
        )
        self.app = app
        self.plugins = plugins

    def _create_runner(self, adk_agent, user_id, app_name):
        return Runner(
            app=self.app,
            session_service=self._session_manager._session_service,
            artifact_service=self._artifact_service,
            memory_service=self._memory_service,
            credential_service=self._credential_service,
            plugins=self.plugins,
        )

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