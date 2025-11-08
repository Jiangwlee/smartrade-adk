from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

from backend.llm import get_glm_model

from .market_analysts import market_analysts_agent
from .stock_analysts import stock_analyst_agent
from ...agent_utils import print_before_model_information

analysts_team = LlmAgent(
    name="analysts_team",
    model=get_glm_model(),
    instruction="You are the coordinator of the analysts team. Your job is to delegate tasks to sub agents.",
    description="Coordinator of the analysts team. Delegate tasks to sub agents.",
    sub_agents=[market_analysts_agent, stock_analyst_agent],
    before_model_callback=print_before_model_information
)