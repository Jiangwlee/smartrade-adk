from datetime import datetime, timezone, timedelta
from typing import Optional

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from backend.llm import get_glm_model

from .sub_agents.analysts_team import analysts_team

def setup_session(
    callback_context: CallbackContext
) -> Optional[LlmResponse]:
    callback_context.state['current_time'] = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S %A")
    return None

ashare_coordinator = LlmAgent(
    name="ashare_coordinator",
    model=get_glm_model(),
    description="An interactive coordinator agent. Responsible for interaction with the user and coordinating sub-agents to fulfill user requests related to A-share market analysis and trading.",
    instruction=(
        "You are a helpful agent who can help users by coordinate sub agents. You should delegate tasks to the appropriate sub-agents based on user requests and compile their responses into a coherent answer."
        "You should respond to the user request only if a user request is not suitable for any sub agent."
    ),
    sub_agents=[
        analysts_team,
    ],
    before_agent_callback=setup_session
)

root_agent = ashare_coordinator