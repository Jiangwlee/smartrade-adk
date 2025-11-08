
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.langchain_tool import LangchainTool
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from langchain_community.tools import TavilySearchResults

from backend.llm import get_doubao_model, get_glm_model, get_deepseek_model
import backend.crawlers.taoguba.tgb_jinghua as tgb_crawler
import backend.crawlers.tonghuashun.ths_hot_board as ths_crawler

from ...agent_utils import suppress_output_callback, print_before_model_information

# Instantiate LangChain tool
tavily_search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
)

# Wrap with LangchainTool
adk_tavily_tool = LangchainTool(tool=tavily_search)

# Crawlers
async def get_tgb_jinghua(tool_context: ToolContext) -> dict:
    """
    获取淘股吧精华热帖

    Returns:
        dict: status and result or error msg.
    """
    posts = await tgb_crawler.crawl()
    if posts:
        header = "# 淘股吧热帖\n\n"
        contents = [f"## {x.title} - 作者：{x.author}\n\n{x.content}" for x in posts]
        posts_str = header + "\n\n---\n\n".join(contents)
        return {"status": "success", "result": posts_str}
    else:
        return {"status": "fail", "result": None} 

GUBA_PROMPT = """你是一个A股市场情绪分析专家，擅长通过散户言论分析市场情绪。
请使用`get_tgb_jinghua`工具获取淘股吧热帖，分析市场情绪、赚钱效应、机会与风险，并生成详细的分析报告。

分析技巧：
- 洞悉市场情绪：散户对于当下和未来市场走势的看法，市场所处阶段，赚钱和亏钱效应如何，选择持股还是持币，选择打板还是低吸...
- 识别市场风险：当前市场中存在哪些潜在风险，散户对于市场风险的态度，选择规避还是拥抱风险...
- 识别市场龙头：从热帖中找出最受关注的龙头个股，说明选择理由...

输出格式：
```markdown
# 淘股吧热帖分析报告

## 情绪分析

## 赚钱效应

## 市场风险

## 核心个股

[核心个股1]：市场地位、散户看法、上涨原因分析
[核心个股2]：市场地位、散户看法、上涨原因分析

## 精选言论

[作者名称1]：[言论内容]
[作者名称2]：[言论内容]
...
```

现在，立即开始分析。
"""

analyze_guba = LlmAgent(
    model=get_glm_model(),
    name="analyze_guba",
    description="淘股吧精华热帖分析专家，擅长分析市场情绪、赚钱效应、机会与风险.",
    instruction=GUBA_PROMPT,
    tools=[get_tgb_jinghua],
    include_contents='none',
)
      
async def get_ths_hot_boards(tool_context: ToolContext, datestr: str, delta: int = 5) -> dict:
    """
    获取同花顺热门板块

    Args:
        datestr (str): 日期，格式为 YYYYMMDD, 比如：20250101。
        delta (int): 获取最近几天的数据，默认为5天。

    Returns:
        dict: status and result or error msg.
    """
    result = await ths_crawler.crawl(date=datestr, delta=delta)
    if result:
        return {"status": "success", "result": result}
    else:
        return {"status": "fail", "result": None}  
    
HOT_BOARD_PROMPT = """你是一个A股热门板块分析专家，擅长通过数据分析市场赚钱效应。
请使用`get_ths_hot_boards`工具获取同花顺热榜数据，分析市场情绪、赚钱效应、市场机会，并生成详细的分析报告。

通过分析连板天梯中的连板个股数量、连板高度、板块热度等数据，识别市场情绪周期，洞悉机会，识别风险，并给出投资建议。
重点分析各个热门板块的表现，找出存在持续性赚钱效应的板块，分析龙头个股，找出上涨动能。

分析技巧：
1. 从宏观到微观：大势 -> 板块 -> 个股
2. 从情绪到操作：情绪 -> 机会与风险 -> 投资建议
3. 从情绪周期分析：冰点启动 -> 发酵主升 -> 高潮分化 -> 绝望退潮

输出格式：
```markdown
# A股热门板块分析报告

## 情绪分析

[以数据为支撑，分析当下所处的情绪周期，给出详细判断理由]

## 赚钱效应

[分析市场的赚钱效应，说明哪些板块存在持续性赚钱效应，以数据为支撑（涨停数量、连板数量、最高连板、连涨天数），分析板块上涨原因，热点轮动趋势]

## 核心个股

[核心个股1]：市场地位、上涨原因
[核心个股2]：市场地位、上涨原因
```

注意事项：
1. A股的开市时间为每个工作日的上午9:30至下午3:00。如果当天没有开市，或者还没有收市（15:00之前），则使用最近一次的开市数据进行分析。比如：当前时间为2025年10月30日14:00，则使用2025年10月29日的收市数据进行分析；当前时间为2025年10月12日（周日），则使用2025年10月10日的收市数据进行分析。
2. 默认查询最近5天的热门板块数据。

当前时间：
{current_time}

现在，立即开始分析。
"""

analyze_hot_board = LlmAgent(
    model=get_glm_model(),
    name="analyze_hot_board",
    description="同花顺热门板块分析专家，擅长分析市场情绪、挖掘赚钱机会.",
    instruction=HOT_BOARD_PROMPT,
    tools=[get_ths_hot_boards],
    include_contents='none',
)
    
INSTRUCTION = """
你是股票市场情绪分析专家。通过分析同花顺热门板块数据、连板天梯、淘股吧热帖，洞悉当前股票市场情绪，识别赚钱效应与市场风险，并生成详细的分析报告。

工作流程：
1. 获取市场数据：
    - 使用`analyze_hot_board`工具获取同花顺热门板块分析结果。
    - 使用`analyze_guba`工具获取淘股吧热帖分析结果。
    - 使用`adk_tavily_tool`工具搜索今日市场信息，包括并不限于：复盘、重要公告、宏观政策...
2. 洞悉市场情绪：散户对于当下和未来市场走势的看法，市场所处阶段，赚钱和亏钱效应如何，选择持股还是持币，选择打板还是低吸...
3. 识别赚钱效应：当前市场中哪些板块和个股表现强势，资金流入情况，市场热点轮动趋势...
4. 识别市场风险：当前市场中存在哪些潜在风险，散户对于市场风险的态度，选择规避还是拥抱风险...
5. 识别情绪变化：从连板高度、板块热度等维度，判断市场和板块情绪的变化趋势，是趋向乐观还是悲观...
6. 重点个股分析：基于热帖，挑选3-5只最受投资者关注个股进行深入分析，说明选择理由，使用`adk_tavily_tool`搜索个股信息，找出个股上涨原因。

分析技巧：
1. 从宏观到微观：大势 -> 板块 -> 个股
2. 从情绪到操作：情绪 -> 机会与风险 -> 投资建议
3. 从情绪周期分析：冰点启动 -> 发酵主升 -> 高潮分化 -> 绝望退潮

注意事项：
1. A股的开市时间为每个工作日的上午9:30至下午3:00。如果当天没有开市，或者还没有收市（15:00之前），则使用最近一次的开市数据进行分析。比如：当前时间为2025年10月30日14:00，则使用2025年10月29日的收市数据进行分析；当前时间为2025年10月12日（周日），则使用2025年10月10日的收市数据进行分析。

输出格式：
```markdown
# A股市场分析报告 - [日期]

## 情绪周期

[明确判断当前市场情绪周期，给出详细判断理由]

## 散户情绪

[分析散户情绪，给出看多/犹豫/看空/恐慌等结论，说明理由]

[精选散户言论]

## 赚钱效应

[分析市场的赚钱效应，说明哪些板块存在持续性赚钱效应，以数据为支撑（涨停数量、连板数量、最高连板、连涨天数），分析板块上涨原因，热点轮动趋势]

## 市场风险

[分析市场的主要风险，说明风险来源及散户态度]

## 核心个股

[分析当下市场的核心个股的市场地位、带动作用、上涨原因等]

## 投资建议

[给出明确的投资建议，包括但不限于：仓位分配、操作建议（买入/持有/卖出/观望等），说明理由]

[从大势、热点、节奏等维度，给出具体个股操作建议]
```

当前时间：
{current_time}

现在，立即开始分析。
"""

market_analysts_agent = LlmAgent(
    model=get_deepseek_model(),
    # model='gemini-2.0-flash',
    name="market_analysts_agent",
    description="A股市场分析专家，擅长分析市场整体情绪、赚钱效应、机会与风险.",
    instruction=INSTRUCTION,
    output_key="market_analysts_report",
    tools=[AgentTool(analyze_hot_board), AgentTool(analyze_guba), adk_tavily_tool],
    before_model_callback=print_before_model_information,
    include_contents='none',
)