
from google.adk import Agent
from google.adk.tools import google_search

MODEL = "gemini-2.5-flash"

RESEARCH_TEAM_PROMPT = """你是研究管理团队的Team Leader，负责提供多空佐证。
"""

research_analyst_agent = Agent(
    model=MODEL,
    name="research_analyst",
    instruction=RESEARCH_TEAM_PROMPT,
    output_key="research_analysis_output",
)