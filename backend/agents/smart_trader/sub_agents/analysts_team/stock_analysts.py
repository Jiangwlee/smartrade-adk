"""
个股分析专家，对个股进行全面分析.
"""
import os
import pandas as pd
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, AgentTool
from google.adk.tools.langchain_tool import LangchainTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StdioServerParameters

from langchain_community.tools import TavilySearchResults
from dataclasses import asdict
from backend.crawlers.jinrongjie.jrj import HangQingType
from backend.llm import get_deepseek_model, get_glm_model
from ...utils.kline_helper import KlineHelper
from ...agent_utils import suppress_output_callback

import backend.crawlers.jinrongjie.jrj as jrj_crawler

ANALYSYS_TEAM_PROMPT = """你是分析师团队的Team Leader，负责市场数据的分析。
"""
# Instantiate LangChain tool
tavily_search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
)

tavily_search_lite = TavilySearchResults(
    max_results=5,
    include_answer=True,
    include_raw_content=False,
    include_images=False,
)

# Wrap with LangchainTool
adk_tavily_tool = LangchainTool(tool=tavily_search)
adk_tavily_tool_lite = LangchainTool(tool=tavily_search_lite)

# Crawler
async def get_stock_hangqing(tool_context: ToolContext, code: str, name: str) -> dict:
    """
    获取过去240个交易日的股票行情数据.

    Args:
        code (str): 股票代码，例如 '000001'
        name (str): 股票名称，例如 '平安银行'

    Returns:
        dict: status and result or error msg.
    """
    hangqing_data = await jrj_crawler.crawl(
        code=code,
        name=name,
        hangqing_type=HangQingType.DAY,
        date=None,
        range_num=240
    )
    if hangqing_data:
        hangqing_data = [asdict(x) for x in hangqing_data]
        tool_context.state["temp:stock_hangqing"] = hangqing_data

        # 转换为 DataFrame 并计算移动平均线
        df = pd.DataFrame(hangqing_data)

        # 按时间排序（从旧到新）
        df = df.sort_values('time').reset_index(drop=True)

        # 计算移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma30'] = df['close'].rolling(window=30).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        df['ma120'] = df['close'].rolling(window=120).mean()

        # 判断红绿柱（收盘价 > 开盘价为红柱，否则为绿柱）
        df['is_red'] = df['close'] > df['open']

        # 取最近30个交易日
        recent_30 = df.tail(30)
        recent_7 = df.tail(7)

        # 统计红绿柱比例
        red_count_7 = recent_7['is_red'].sum()
        red_ratio_7 = (red_count_7 / 7) * 100

        red_count_30 = recent_30['is_red'].sum()
        red_ratio_30 = (red_count_30 / 30) * 100

        # 获取最新一天的数据
        latest = df.iloc[-1]

        # 格式化均线数据
        ma5_str = f"{latest['ma5']:.2f}" if pd.notna(latest['ma5']) else 'N/A'
        ma10_str = f"{latest['ma10']:.2f}" if pd.notna(latest['ma10']) else 'N/A'
        ma20_str = f"{latest['ma20']:.2f}" if pd.notna(latest['ma20']) else 'N/A'
        ma30_str = f"{latest['ma30']:.2f}" if pd.notna(latest['ma30']) else 'N/A'
        ma60_str = f"{latest['ma60']:.2f}" if pd.notna(latest['ma60']) else 'N/A'
        ma120_str = f"{latest['ma120']:.2f}" if pd.notna(latest['ma120']) else 'N/A'

        # 生成文字报告
        report = f"""## 股票行情数据分析

**短期走势强度分析：**
- 最近7个交易日：红柱{red_count_7}根，占比{red_ratio_7:.2f}%
- 最近30个交易日：红柱{red_count_30}根，占比{red_ratio_30:.2f}%

**今日技术指标：**
- 日期：{latest['time']}
- 开盘：{latest['open']:.2f}
- 收盘：{latest['close']:.2f}
- 最高：{latest['high']:.2f}
- 最低：{latest['low']:.2f}
- 涨跌：{'红柱(上涨)' if latest['is_red'] else '绿柱(下跌)'}
- MA5：{ma5_str}
- MA10：{ma10_str}
- MA20：{ma20_str}
- MA30：{ma30_str}
- MA60：{ma60_str}
- MA120：{ma120_str}
"""

        return {"status": "success", "result": report}
    else:
        return {"status": "fail", "result": None}
    
def create_kline(tool_context: ToolContext) -> str:
    """
    创建K线图

    Returns:
        str: K线图文件路径
    """
    helper = KlineHelper()
    kline = helper.create_kline(tool_context.state["temp:stock_hangqing"])
    return {"status": "success", "result": str(kline)}

image_tool = MCPToolset(
    connection_params=StdioConnectionParams(
        timeout=300,
        server_params = StdioServerParameters(
            command='npx',
            args=[
                "-y",  # Argument for npx to auto-confirm install
                "@z_ai/mcp-server",
            ],
            env={
                "Z_AI_API_KEY": os.environ.get("Z_AI_API_KEY"),
                "Z_AI_MODE": "ZHIPU"
            }
        ),
    ),
    # Optional: Filter which tools from the MCP server are exposed
    # tool_filter=['list_directory', 'read_file']
)

STOCK_BASIS_ANALYZE_PROMPT = """
你是一个职业的股票交易员，你的任务是对股票进行全面的基本面分析。

用户将告诉你一只股票名称或者代码，你可以使用如下工具获取必要信息：
1. **adk_tavily_tool**: 使用adk_tavily_tool搜索引擎获取股票的基本面信息、最近三年的财务信息和最新资讯

分析技巧：
1. 基本面分析：分析股票的基本面信息，包括营收、利润变化情况、公司治理、行业地位等。
2. 消息面分析：分析市场最新资讯，包括政策、研报、行业动态、公司公告等。
3. 结合基本面、消息面，生成基本面分析报告。

分析要求：
1. 尊重事实，不夸大事实，不主观臆断。

分析报告格式：
```
# [股票名称-股票代码] 股票基本面分析报告

## 基本面分析

[以数据为支撑，详细分析公司在最近三年的营收、利润变化情况]

[分析公司所处的行业地位、竞争格局和发展前景]

[分析公司股票当前的估值情况，预期成长空间]

## 消息面分析

[分析公司的最新公告、行业动态、政策等，分析消息面对于公司股价是利多还是利空]

```
当前时间：
{current_time}

请开始进行分析。
"""

analyze_stock_basis = LlmAgent(
    model=get_glm_model(),
    name="analyze_stock_basis",
    description="股票基本面分析专家，对具体股票进行全面分析",
    instruction=STOCK_BASIS_ANALYZE_PROMPT,
    tools=[adk_tavily_tool],
    include_contents='none',
)

STOCK_ANALYZE_PROMPT = """
你是一个专业而自律的股票作手，对市场有敏锐的洞察力，擅长趋势交易，严格控制风险。你的任务是基于市场分析报告，结合个股走势，给出买卖建议。

用户将告诉你一只股票名称或者代码，你可以使用如下工具获取必要信息：
1. **analyze_stock_basis**: 当进行股票基本面和消息面分析时，调用此工具
2. **get_stock_hangqing**: 获取过去240个交易日的股票行情数据
3. **create_kline**: 创建K线图
4. **image_tool**: 对K线图进行技术分析
5. **adk_tavily_tool_lite**: 搜索获取股票相关信息，注意消息的时效性。当前时间为：{current_time}

工作流程：
1. 获取基本面分析和消息面分析报告：使用`analyze_stock_basis`获取股票基本面和消息面分析报告。**注意：不需要额外搜索公司相关资讯！**
2. 技术面分析：使用`get_stock_hangqing`获取股票行情，使用`create_kline`创建K线图，使用`image_tool`分析K线图。
3. 结合基本面、技术面、消息面，以及市场分析报告，给出交易建议。

市场分析报告：
{market_analysis_report?}

分析报告格式：
```
# [股票名称-股票代码] 股票分析报告

## 基本面分析

[以数据为支撑，分析公司在过去三年的营收、利润变化情况]
[分析公司所处的行业地位、竞争格局和发展前景]

## 技术面分析

[深度解析股票的K线图，包括趋势、均线、MACD、量能等指标，分析股票的趋势、位置、支撑和阻力等。分析时注意数据的时效性，使用get_stock_hangqing获取近期的价格数据，进行网络搜索时也可以加上当前时间。]

[分别分析最近7个交易日和30个交易日的红柱、绿柱比例，红柱越多，走势越强劲，持股体验越好。分析短期和中期的走势强度。]

## 消息面分析

[分析公司的最新公告、行业动态、政策等，分析消息面对于公司股价是利多还是利空]

## 交易建议

[你一共有100万资金，打算买入5只股票。作为一个稳健的趋势投资者，请给出当前股票的交易决策，你是否愿意买入？如果愿意买入，最小投入仓位与最大投入仓位分别是多少？并给出理由。交易建议应当合理，不得出现自相矛盾的建议，比如：“在46元至48元分批买入，跌破47元止损”，止损价47元高于买入价46元是不合理的]
```

当前时间为：{current_time}

请开始进行分析。
"""

stock_analyst_agent = LlmAgent(
    model=get_deepseek_model(),
    name="stock_analyst_agent",
    description="股票分析专家，对具体股票进行全面分析",
    instruction=STOCK_ANALYZE_PROMPT,
    tools=[AgentTool(analyze_stock_basis), adk_tavily_tool_lite, get_stock_hangqing, create_kline, image_tool],
    include_contents='none'
)