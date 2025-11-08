"""金融界网站爬虫

https://www.jrj.com/

主要作用：
1. 爬取股票的价格：包括分钟线、日线、周线、月线等
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel

from ..base import CrawlerNonRetryableError, create_http_client, retry_on_error

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class StockHangQingInfo:
    """股票行情信息"""

    code: str  # 股票代码
    name: str  # 股票名称
    time: int  # 时间，日期或者时间戳：20241213或者1733103000
    open: float  # 开盘价
    high: float  # 最高价
    low: float  # 最低价
    close: float  # 收盘价
    volume: int  # 成交量
    amount: float  # 成交金额


class HangQingType(Enum):
    """行情类型"""

    DAY = "day"  # 日线
    ONE_M = "1minkline"  # 1分钟线


# ============================================================================
# 数据转换函数
# ============================================================================


def _transform_data(raw_data: dict[str, Any], code: str, name: str) -> list[StockHangQingInfo]:
    """转换原始数据为 StockHangQingInfo 列表

    Args:
        raw_data: 原始JSON响应数据
        code: 股票代码
        name: 股票名称

    Returns:
        StockHangQingInfo 列表

    Raises:
        CrawlerNonRetryableError: 数据解析失败
    """
    try:
        # 处理可能的嵌套JSON结构
        if isinstance(raw_data, dict) and "value" in raw_data:
            inner_data = raw_data.get("value")
            if isinstance(inner_data, str):
                import json

                raw_data = json.loads(inner_data)

        # 处理不同的数据格式
        kline_data = None
        if isinstance(raw_data, dict):
            # 尝试获取 kline 数据（可能在不同的位置）
            if "kline" in raw_data:
                kline_data = raw_data.get("kline", [])
            elif "data" in raw_data and isinstance(raw_data["data"], dict):
                kline_data = raw_data["data"].get("kline", [])
            elif isinstance(raw_data, list):
                kline_data = raw_data

        if not kline_data:
            raise ValueError(f"响应数据格式不正确: {raw_data}")

        # 转换每条 K 线数据
        hangqing_list = []
        for item in kline_data:
            time = item.get("time") or item.get("nTime", 0)
            open_val = item.get("open") or item.get("nOpenPx", 0)
            high_val = item.get("high") or item.get("nHighPx", 0)
            low_val = item.get("low") or item.get("nLowPx", 0)
            close_val = item.get("close") or item.get("nLastPx", 0)
            volume_val = item.get("volume") or item.get("llVolume", 0)
            amount_val = item.get("amount") or item.get("llValue", 0)

            hangqing = StockHangQingInfo(
                code=code,
                name=name,
                time=int(time),
                open=float(open_val) / 10000 if open_val and open_val > 100000 else float(open_val),
                high=float(high_val) / 10000 if high_val and high_val > 100000 else float(high_val),
                low=float(low_val) / 10000 if low_val and low_val > 100000 else float(low_val),
                close=(
                    float(close_val) / 10000 if close_val and close_val > 100000 else float(close_val)
                ),
                volume=int(volume_val),
                amount=float(amount_val),
            )
            hangqing_list.append(hangqing)

        return hangqing_list

    except Exception as e:
        logger.error(f"数据转换失败: {e}")
        raise CrawlerNonRetryableError(f"数据转换失败: {e}") from e


# ============================================================================
# 辅助函数
# ============================================================================


def _build_security_id(code: str) -> str:
    """根据股票代码构造 security_id

    Args:
        code: 股票代码

    Returns:
        security_id (沪深京A股：6 开头 -> 1xxxxxx，深圳股票 -> 2xxxxxx)
    """
    return f"1{code}" if code.startswith("6") else f"2{code}"


def _build_url(
    code: str,
    hangqing_type: HangQingType,
    date: str,
    range_num: int = 60,
) -> str:
    """构造请求 URL

    Args:
        code: 股票代码
        hangqing_type: 行情类型
        date: 开始日期（格式：20241213）
        range_num: 范围，往前取多少条数据

    Returns:
        完整的请求URL
    """
    security_id = _build_security_id(code)
    return (
        f"https://gateway.jrj.com/quot-kline"
        f"?format=json"
        f"&securityId={security_id}"
        f"&type={hangqing_type.value}"
        f"&direction=left"
        f"&range.num={range_num}"
        f"&range.begin={date}"
    )


@retry_on_error(max_attempts=3, delay=1.0, backoff=2.0)
async def _fetch_kline_data(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    """异步获取K线数据

    Args:
        client: httpx 异步客户端
        url: API URL

    Returns:
        JSON响应数据
    """
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


# ============================================================================
# 爬虫函数
# ============================================================================


async def crawl(
    code: str,
    name: str,
    hangqing_type: HangQingType = HangQingType.DAY,
    date: str | None = None,
    range_num: int = 60,
) -> list[StockHangQingInfo]:
    """爬取金融界股票行情数据

    Args:
        code: 股票代码（如 '002593'）
        name: 股票名称（如 '老百姓'）
        hangqing_type: 行情类型（DAY 或 ONE_M）
        date: 开始日期（格式：20241213），如果为None则使用今天
        range_num: 范围，往前取多少条数据

    Returns:
        StockHangQingInfo 列表

    Example:
        >>> # 获取日线数据
        >>> data = await crawl("002593", "老百姓")
        >>> for item in data:
        ...     print(f"{item.time}: {item.close}")

        >>> # 获取分钟线数据
        >>> data = await crawl(
        ...     "002593", "老百姓",
        ...     hangqing_type=HangQingType.ONE_M,
        ...     date="20241213"
        ... )
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")

    logger.info(f"开始爬取: {code}-{name}, 类型: {hangqing_type.value}, 日期: {date}")

    # 构建URL
    url = _build_url(code, hangqing_type, date, range_num)
    logger.debug(f"请求 URL: {url}")

    async with create_http_client(
        timeout=10.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    ) as client:
        try:
            # 获取数据
            raw_data = await _fetch_kline_data(client, url)
            logger.debug(f"爬取结果: {raw_data}")

            # 转换数据
            hangqing_list = _transform_data(raw_data, code, name)
            logger.info(f"爬取成功！获取到 {len(hangqing_list)} 条数据")
            return hangqing_list

        except Exception as e:
            logger.exception(f"爬取异常: {e}")
            raise
