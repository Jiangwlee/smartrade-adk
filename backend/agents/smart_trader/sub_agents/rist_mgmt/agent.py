
from google.adk import Agent
from google.adk.tools import google_search

MODEL = "gemini-2.5-flash"

TRADE_TEAM_PROMPT = """你是风险管理团队的Team Leader，负责评估交易风险。
"""

risk_analyst_agent = Agent(
    model=MODEL,
    name="risk_analyst_agent",
    instruction=TRADE_TEAM_PROMPT,
    output_key="risk_analysis_output",
)