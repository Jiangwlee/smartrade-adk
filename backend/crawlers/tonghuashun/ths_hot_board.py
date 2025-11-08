"""同花顺热门板块爬虫

从同花顺数据API获取连板天梯和最强板块数据，输出Markdown格式报告。

API端点:
1. 连板天梯: https://data.10jqka.com.cn/dataapi/limit_up/continuous_limit_up
2. 最强板块: http://data.10jqka.com.cn/dataapi/limit_up/block_top
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, Field

from ..base import CrawlerNonRetryableError, create_http_client, retry_on_error

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


class ContinuousLimitUpStock(BaseModel):
    """连板天梯股票模型"""

    code: str = Field(description="股票代码")
    name: str = Field(description="股票名称")
    continue_num: int = Field(description="连板天数")


class ContinuousLimitUpLevel(BaseModel):
    """连板天梯层级模型"""

    height: int = Field(description="连板高度")
    count: int = Field(description="该高度股票数量")
    stocks: list[ContinuousLimitUpStock] = Field(description="股票列表")


class BlockLimitUpStock(BaseModel):
    """板块内涨停股模型"""

    code: str = Field(description="股票代码")
    name: str = Field(description="股票名称")
    change_rate: float = Field(description="涨幅(%)")
    continue_num: int = Field(description="连板天数")
    high: str = Field(description="连板描述(如'首板','2连板')")
    latest: float = Field(description="最新价格")
    reason_type: str = Field(description="涨停原因标签")
    reason_info: str = Field(description="详细涨停原因(AI生成)")


class TopBlock(BaseModel):
    """最强板块模型"""

    code: str = Field(description="板块代码")
    name: str = Field(description="板块名称")
    change: float = Field(description="板块涨跌幅(%)")
    limit_up_count: int = Field(description="涨停股数量")
    continuous_plate_count: int = Field(description="连板股数量")
    high_desc: str = Field(description="最高连板描述")
    active_days: int = Field(description="活跃天数")
    stocks: list[BlockLimitUpStock] = Field(description="涨停股列表")


class ThsHotBoardData(BaseModel):
    """同花顺热门板块数据"""

    date: str = Field(description="行情日期(YYYYMMDD)")
    continuous_limit_up: list[ContinuousLimitUpLevel] = Field(description="连板天梯")
    top_blocks: list[TopBlock] = Field(description="最强板块")


# ============================================================================
# 数据转换函数
# ============================================================================


def _transform_data(raw_data: dict[str, Any]) -> ThsHotBoardData:
    """转换原始数据为 ThsHotBoardData 对象

    Args:
        raw_data: 包含 continuous_limit_up、block_top 和 date 的字典

    Returns:
        ThsHotBoardData 对象

    Raises:
        CrawlerNonRetryableError: 数据解析失败
    """
    try:
        continuous_data = raw_data.get("continuous_limit_up", {})
        block_data = raw_data.get("block_top", {})
        date = raw_data.get("date", "")

        # 解析连板天梯
        continuous_levels: list[ContinuousLimitUpLevel] = []
        if continuous_data.get("status_code") == 0:
            for level_data in continuous_data.get("data", []):
                level_stocks = [
                    ContinuousLimitUpStock(
                        code=stock["code"],
                        name=stock["name"],
                        continue_num=stock["continue_num"],
                    )
                    for stock in level_data.get("code_list", [])
                ]
                continuous_levels.append(
                    ContinuousLimitUpLevel(
                        height=level_data["height"],
                        count=level_data["number"],
                        stocks=level_stocks,
                    ),
                )

        # 解析最强板块
        top_blocks: list[TopBlock] = []
        if block_data.get("status_code") == 0:
            for block in block_data.get("data", []):
                block_stocks: list[BlockLimitUpStock] = [
                    BlockLimitUpStock(
                        code=stock["code"],
                        name=stock["name"],
                        change_rate=stock["change_rate"],
                        continue_num=stock["continue_num"],
                        high=stock["high"],
                        latest=stock["latest"],
                        reason_type=stock.get("reason_type") or "",
                        reason_info=stock.get("reason_info") or "",
                    )
                    for stock in block.get("stock_list", [])
                ]
                top_blocks.append(
                    TopBlock(
                        code=block["code"],
                        name=block["name"],
                        change=block["change"],
                        limit_up_count=block["limit_up_num"],
                        continuous_plate_count=block["continuous_plate_num"],
                        high_desc=block["high"],
                        active_days=block["days"],
                        stocks=block_stocks,
                    ),
                )

        return ThsHotBoardData(
            date=date, continuous_limit_up=continuous_levels, top_blocks=top_blocks,
        )

    except Exception as e:
        logger.error(f"Failed to parse THS hot board data: {e}")
        raise CrawlerNonRetryableError(f"Data parsing failed: {e}") from e


# ============================================================================
# 辅助函数
# ============================================================================


def _generate_candidate_dates(end_date: str, num_days: int = 30) -> list[str]:
    """生成候选日期列表（包含周末和节假日）

    Args:
        end_date: 结束日期(YYYYMMDD)
        num_days: 往前推的天数（默认30天，覆盖至少20个交易日）

    Returns:
        日期列表，格式为YYYYMMDD，按时间倒序排列
    """
    end_dt = datetime.strptime(end_date, "%Y%m%d")
    dates = []
    for i in range(num_days):
        date = end_dt - timedelta(days=i)
        dates.append(date.strftime("%Y%m%d"))
    return dates


def _build_url(base_url: str, date: str, filter_str: str = "HS,GEM2STAR") -> str:
    """构建API URL

    Args:
        base_url: API基础URL
        date: 日期(YYYYMMDD)
        filter_str: 过滤器字符串

    Returns:
        完整URL
    """
    return f"{base_url}?filter={filter_str}&date={date}"


@retry_on_error(max_attempts=3, delay=1.0, backoff=2.0)
async def _fetch_api(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    """异步获取API数据

    Args:
        client: httpx 异步客户端
        url: API URL

    Returns:
        JSON响应数据
    """
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


async def _fetch_single_date(
    client: httpx.AsyncClient, date: str
) -> ThsHotBoardData | None:
    """异步抓取单个日期的数据

    Args:
        client: httpx 异步客户端
        date: 行情日期,格式YYYYMMDD

    Returns:
        ThsHotBoardData对象，如果该日期无数据则返回None
    """
    try:
        # 并发请求两个API
        base_url_continuous = (
            "https://data.10jqka.com.cn/dataapi/limit_up/continuous_limit_up"
        )
        base_url_block = "http://data.10jqka.com.cn/dataapi/limit_up/block_top"

        url_continuous = _build_url(base_url_continuous, date)
        url_block = _build_url(base_url_block, date)

        continuous_task = _fetch_api(client, url_continuous)
        block_task = _fetch_api(client, url_block)

        results = await asyncio.gather(continuous_task, block_task, return_exceptions=True)
        continuous_data = results[0]
        block_data = results[1]

        # 检查是否有异常
        if isinstance(continuous_data, Exception):
            logger.warning(f"Failed to fetch continuous data for {date}: {continuous_data}")
            return None
        if isinstance(block_data, Exception):
            logger.warning(f"Failed to fetch block data for {date}: {block_data}")
            return None

        # 检查是否是有效交易日（status_code为0表示有数据）
        if continuous_data.get("status_code") != 0 and block_data.get("status_code") != 0:
            logger.debug(f"No trading data for {date}")
            return None

        # 合并数据并转换
        combined_data: dict[str, Any] = {
            "date": date,
            "continuous_limit_up": continuous_data,
            "block_top": block_data,
        }

        parsed_data = _transform_data(combined_data)
        return parsed_data

    except Exception as e:
        logger.warning(f"Error fetching data for {date}: {e}")
        return None


def _generate_markdown_report(data: ThsHotBoardData, top_blocks_limit: int = 5) -> str:
    """生成Markdown格式报告

    Args:
        data: 解析后的数据
        top_blocks_limit: 最强板块输出数量限制

    Returns:
        Markdown格式的报告
    """
    lines = []

    # 标题
    formatted_date = f"{data.date[:4]}年{data.date[4:6]}月{data.date[6:8]}日"
    lines.append(f"# 同花顺热门板块 - {formatted_date}\n")

    # 一、连板天梯
    lines.append("## 一、连板天梯\n")
    lines.append("| 高度 | 数量 | 股票列表 |")
    lines.append("|------|------|----------|")

    for level in data.continuous_limit_up:
        height_text = f"{level.height}连板"
        stock_list = ", ".join([f"{s.name}({s.code})" for s in level.stocks])
        lines.append(f"| {height_text} | {level.count} | {stock_list} |")

    # 连板总结
    total_stocks = sum(level.count for level in data.continuous_limit_up)
    max_height = max((level.height for level in data.continuous_limit_up), default=0)
    max_stock = (
        data.continuous_limit_up[0].stocks[0].name
        if data.continuous_limit_up and data.continuous_limit_up[0].stocks
        else "N/A"
    )
    lines.append(
        f"\n**连板天梯总结**: 最高{max_height}连板({max_stock}), "
        f"共{len(data.continuous_limit_up)}个层级, {total_stocks}只连板股\n",
    )

    # 二、最强板块
    lines.append(f"## 二、最强板块 Top {top_blocks_limit}\n")

    for idx, block in enumerate(data.top_blocks[:top_blocks_limit], start=1):
        lines.append(f"### {idx}. {block.name} ({block.code})")
        lines.append(
            f"- **涨停数**: {block.limit_up_count}只 | "
            f"**连板数**: {block.continuous_plate_count}只 | "
            f"**板块涨跌**: {block.change:+.2f}%",
        )
        lines.append(
            f"- **最高连板**: {block.high_desc} | " f"**活跃天数**: {block.active_days}天",
        )
        lines.append("- **核心个股**:\n")

        # 显示前3只涨停股
        for stock in block.stocks[:3]:
            lines.append(
                f"  **{stock.name}({stock.code})**: {stock.change_rate:+.2f}%, {stock.high}",
            )
            lines.append(f"  - 原因标签: {stock.reason_type}")
            lines.append(f"  - 详细原因: {stock.reason_info}\n")

    return "\n".join(lines)


# ============================================================================
# 爬虫函数
# ============================================================================


async def crawl(date: str, delta: int = 1, top_blocks_limit: int = 5) -> str:
    """爬取同花顺热门板块数据

    Args:
        date: 结束日期，格式YYYYMMDD（如"20251030"）
        delta: 要返回的交易日数量（1-10），默认为1
        top_blocks_limit: 最强板块输出数量限制

    Returns:
        Markdown格式的分析报告，多天数据用---分隔

    Example:
        >>> report = await crawl("20251030")
        >>> print(report)

        >>> # 获取最近3个交易日
        >>> report = await crawl("20251030", delta=3)
    """
    # 限制delta范围
    delta = max(1, min(delta, 10))

    logger.info(f"Starting to crawl THS hot board data up to {date}, delta={delta}")

    # 创建 httpx 客户端
    async with create_http_client(
        timeout=20.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://data.10jqka.com.cn/",
        },
    ) as client:
        # 生成候选日期（往前推30天以确保覆盖足够的交易日）
        candidate_dates = _generate_candidate_dates(date, num_days=30)

        # 并发抓取所有候选日期的数据
        tasks = [_fetch_single_date(client, d) for d in candidate_dates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤出有效的交易日数据
        valid_data: list[tuple[str, ThsHotBoardData]] = []
        for date_str, result in zip(candidate_dates, results, strict=False):
            if isinstance(result, ThsHotBoardData):
                valid_data.append((date_str, result))

        if not valid_data:
            raise CrawlerNonRetryableError("No valid trading data found in the date range")

        # 按日期倒序排序并取前delta个
        valid_data.sort(key=lambda x: x[0], reverse=True)
        selected_data = valid_data[:delta]

        # 生成组合的Markdown报告
        reports = [
            _generate_markdown_report(data, top_blocks_limit) for _, data in selected_data
        ]
        return "\n\n---\n\n".join(reports)
