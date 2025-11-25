from datetime import datetime, timezone, timedelta
from typing import Optional

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai.types import ThinkingConfig, GenerateContentConfig
from google.adk.planners import BuiltInPlanner, PlanReActPlanner
from backend.llm import get_glm_model
from backend.config.logging import get_logger

from .sub_agents.analysts_team import analysts_team

logger = get_logger(__name__)

def setup_session(
    callback_context: CallbackContext
) -> Optional[LlmResponse]:
    callback_context.state['current_time'] = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S %A")
    return None

# 步骤 1：创建 ThinkingConfig {: #step-1-create-thinkingconfig}
thinking_config = ThinkingConfig(
    include_thoughts=True,   # 要求模型在响应中包含其思考
    thinking_budget=256      # 将"思考"限制为 256 个 token（根据需要调整）
)
logger.info("ThinkingConfig:", thinking_config)

generate_content_config = GenerateContentConfig(
    temperature=0.2, # More deterministic output
    max_output_tokens=8192,
)

# 步骤 2：实例化 BuiltInPlanner {: #step-2-instantiate-builtinplanner}
planner = BuiltInPlanner(
    thinking_config=thinking_config
)
logger.info("BuiltInPlanner 已创建。")

ashare_coordinator = LlmAgent(
    name="ashare_coordinator",
    model=get_glm_model(),
    generate_content_config=generate_content_config,
    description="An interactive coordinator agent. Responsible for interaction with the user and coordinating sub-agents to fulfill user requests related to A-share market analysis and trading.",
    instruction=(
        "You are a helpful agent who can help users by coordinate sub agents. You should delegate tasks to the appropriate sub-agents based on user requests and compile their responses into a coherent answer."
        "You should respond to the user request only if a user request is not suitable for any sub agent."
    ),
    sub_agents=[
        analysts_team,
    ],
    planner=planner,
    before_agent_callback=setup_session
)

root_agent = ashare_coordinator