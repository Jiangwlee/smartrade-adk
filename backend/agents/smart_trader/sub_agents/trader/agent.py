
from google.adk import Agent
from google.adk.tools import google_search

MODEL = "gemini-2.5-flash"

TRADE_TEAM_PROMPT = """你是交易员团队的Team Leader，负责制定交易策略。
"""

trade_analyst_agent = Agent(
    model=MODEL,
    name="trade_analyst_agent",
    instruction=TRADE_TEAM_PROMPT,
    output_key="trade_analysis_output",
)