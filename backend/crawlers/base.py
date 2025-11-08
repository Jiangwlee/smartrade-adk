"""爬虫公共基础设施模块

提供所有爬虫共享的基础功能：
- 自定义异常类
- httpx 客户端配置
- 重试装饰器
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# 异常类
# ============================================================================


class CrawlerError(Exception):
    """爬虫基础异常"""

    pass


class CrawlerRetryableError(CrawlerError):
    """可重试的爬虫异常"""

    pass


class CrawlerNonRetryableError(CrawlerError):
    """不可重试的爬虫异常"""

    pass


# ============================================================================
# httpx 客户端配置
# ============================================================================


def create_http_client(
    timeout: float = 20.0,
    headers: dict[str, str] | None = None,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """创建配置好的 httpx 异步客户端

    Args:
        timeout: 请求超时时间（秒）
        headers: 自定义请求头
        **kwargs: 其他 httpx.AsyncClient 参数

    Returns:
        配置好的 httpx.AsyncClient 实例
    """
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
    }

    if headers:
        default_headers.update(headers)

    return httpx.AsyncClient(
        timeout=timeout,
        headers=default_headers,
        follow_redirects=True,
        **kwargs,
    )


# ============================================================================
# 重试装饰器
# ============================================================================


T = TypeVar("T")


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (httpx.HTTPError, CrawlerRetryableError),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_msg = str(e) or f"{type(e).__name__}"
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} 第 {attempt} 次尝试失败: {error_msg}，"
                            f"{current_delay:.1f}秒后重试..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} 达到最大重试次数 {max_attempts}，"
                            f"最后错误: {error_msg}"
                        )
                except CrawlerNonRetryableError as e:
                    logger.error(f"{func.__name__} 遇到不可重试错误: {e}")
                    raise

            # 如果所有重试都失败，抛出最后一个异常
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
