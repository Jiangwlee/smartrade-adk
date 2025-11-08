
from google.adk import Agent
from google.adk.tools import google_search

MODEL = "gemini-2.5-flash"

manager_TEAM_PROMPT = """你是管理团队的Team Leader，负责做出投资决策。
"""

manager_analyst_agent = Agent(
    model=MODEL,
    name="manager_analyst_agent",
    instruction=manager_TEAM_PROMPT,
    output_key="manager_analysis_output",
)