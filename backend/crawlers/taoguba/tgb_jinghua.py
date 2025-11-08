"""淘股吧精华帖爬虫

https://www.tgb.cn/jinghua/1-1

爬取淘股吧精华帖列表，获取每个帖子的详细信息：
- 标题
- 正文
- 作者
- 发帖日期
- 评论数
- 浏览数
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ..base import CrawlerRetryableError, create_http_client, retry_on_error

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class TgbPost:
    """淘股吧帖子数据"""

    title: str
    content: str
    author: str
    publish_date: str
    reply_count: int
    view_count: int
    url: str | None = None


# ============================================================================
# 数据解析函数
# ============================================================================


def _parse_list_page(html: str) -> list[dict[str, Any]]:
    """解析列表页，提取帖子基本信息

    Args:
        html: 列表页HTML

    Returns:
        包含帖子基本信息的列表
    """
    posts = []
    soup = BeautifulSoup(html, "html.parser")

    # 查找所有文章列表项
    articles = soup.find_all("div", class_="Nbbs-tiezi-lists")
    logger.debug(f"找到 {len(articles)} 个文章列表项")

    for article in articles:
        try:
            # 提取标题和URL
            title_link = article.find("a", class_="overhide mw300")
            if not title_link:
                continue

            title_text = title_link.get_text(strip=True)
            post_url = title_link.get("href", "")

            if not title_text or not post_url:
                continue

            # 清理标题（移除[精]等标记）
            title = (
                title_text.replace("[精]", "")
                .replace("[红包]", "")
                .replace("[投票]", "")
                .strip()
            )

            # 提取评论数 (格式: (数字))
            reply_elem = article.find("span", string=re.compile(r"\(\d+\)"))
            reply_count = 0
            if reply_elem:
                match = re.search(r"\((\d+)\)", reply_elem.get_text())
                if match:
                    reply_count = int(match.group(1))

            # 提取浏览数和评论数 (格式: 数字 / 数字)
            view_elem = article.find("div", class_="left middle-list-talk")
            view_count = 0
            if view_elem:
                text = view_elem.get_text(strip=True)
                match = re.search(r"(\d+)\s*/\s*(\d+)", text)
                if match:
                    view_count = int(match.group(2))

            # 提取发帖日期 (格式: MM-DD HH:MM)
            date_elem = article.find("div", class_="left middle-list-post")
            publish_date = ""
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # 匹配 MM-DD HH:MM 或其他日期格式
                match = re.search(r"(\d{2}-\d{2}\s+\d{2}:\d{2})", date_text)
                if match:
                    publish_date = match.group(1)
                else:
                    # 如果是今天，可能格式不同
                    publish_date = date_text

            # 提取作者
            author = ""
            author_link = article.find("a", class_="mw100 overhide")
            if author_link:
                author = author_link.get_text(strip=True)

            # 只添加有标题的帖子
            if title:
                posts.append(
                    {
                        "url": post_url,
                        "title": title,
                        "author": author,
                        "publish_date": publish_date,
                        "reply_count": reply_count,
                        "view_count": view_count,
                    }
                )

        except Exception as e:
            logger.debug(f"解析文章时出错: {e}")
            continue

    logger.info(f"解析列表页成功，找到{len(posts)}个帖子")
    return posts


def _parse_detail_page(html: str) -> str:
    """解析详情页，提取帖子正文内容

    Args:
        html: 详情页HTML

    Returns:
        帖子正文内容
    """
    soup = BeautifulSoup(html, "html.parser")
    content = ""

    # 移除脚本和样式标签
    for script in soup(["script", "style"]):
        script.decompose()

    # 尝试多个内容容器选择器
    content_selectors = [
        ("div", {"id": "article"}),
        ("div", {"class": re.compile(r"article-content|article_content")}),
        ("div", {"class": re.compile(r".*content.*")}),
        ("article", {}),
    ]

    for tag, attrs in content_selectors:
        elem = soup.find(tag, attrs) if attrs else soup.find(tag)
        if elem:
            content = elem.get_text(separator=" ", strip=True)
            if len(content) > 100:
                break
            content = ""

    # 如果还是没有找到，取所有文本
    if not content:
        body = soup.find("body")
        if body:
            content = body.get_text(separator=" ", strip=True)

    # 清理空白
    content = re.sub(r"\s+", " ", content).strip()

    # 限制长度
    if len(content) > 5000:
        content = content[:5000]

    logger.debug(f"解析详情页成功，提取正文{len(content)}个字符")
    return content


# ============================================================================
# 辅助函数
# ============================================================================


@retry_on_error(max_attempts=3, delay=1.0, backoff=2.0)
async def _fetch_page(client: httpx.AsyncClient, url: str) -> str:
    """异步获取页面HTML

    Args:
        client: httpx 异步客户端
        url: 页面URL

    Returns:
        HTML内容
    """
    response = await client.get(url)
    response.raise_for_status()
    return response.text


async def _fetch_detail_page(
    client: httpx.AsyncClient, post_info: dict[str, Any]
) -> TgbPost | None:
    """异步获取单个帖子的详情页

    Args:
        client: httpx 异步客户端
        post_info: 帖子信息字典

    Returns:
        TgbPost 对象或 None（如果获取失败）
    """
    try:
        # 构建完整URL
        if post_info["url"].startswith("http"):
            detail_url = post_info["url"]
        else:
            # 确保URL以斜杠开头，避免拼接错误
            url_path = post_info["url"] if post_info["url"].startswith("/") else f"/{post_info['url']}"
            detail_url = f"https://www.tgb.cn{url_path}"

        # 获取详情页
        try:
            detail_html = await _fetch_page(client, detail_url)
            content = _parse_detail_page(detail_html)
        except Exception as e:
            logger.warning(f"获取详情页失败 {detail_url}: {e}")
            content = ""

        post = TgbPost(
            title=post_info["title"],
            content=content,
            author=post_info["author"],
            publish_date=post_info["publish_date"],
            reply_count=post_info["reply_count"],
            view_count=post_info["view_count"],
            url=detail_url,
        )

        logger.info(f"✅ 完成: {post_info['title'][:50]}... (作者: {post_info['author']})")
        return post

    except Exception as e:
        logger.error(f"处理帖子 {post_info['title']} 时出错: {e}")
        return None


# ============================================================================
# 爬虫函数
# ============================================================================


async def crawl(base_url: str = "https://www.tgb.cn/jinghua/1-1") -> list[TgbPost]:
    """爬取淘股吧精华帖

    Args:
        base_url: 精华帖列表页URL

    Returns:
        帖子列表，每个帖子包含标题、正文、作者、日期、评论数、浏览数

    Example:
        >>> posts = await crawl()
        >>> for post in posts:
        ...     print(f"{post.title} - {post.author}")
    """
    logger.info(f"开始爬取淘股吧精华帖，基础URL: {base_url}")

    async with create_http_client(
        timeout=20.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.tgb.cn/",
        },
    ) as client:
        try:
            # 第一步：爬取列表页
            logger.info("第一步：爬取列表页...")
            list_html = await _fetch_page(client, base_url)
            posts_info = _parse_list_page(list_html)

            if not posts_info:
                logger.warning("列表页中没有找到帖子")
                return []

            logger.info(f"从列表页找到 {len(posts_info)} 个帖子")

            # 过滤：只保留当日发布的帖子
            max_date = None
            for post in posts_info:
                if post.get("publish_date"):
                    publish_date = post["publish_date"].split(" ")[0]
                    if max_date is None or publish_date >= max_date:
                        max_date = publish_date

            # 只保留最新日期的帖子
            if max_date:
                filtered_posts_info = [
                    p
                    for p in posts_info
                    if p.get("publish_date")
                    and p["publish_date"].split(" ")[0] == max_date
                    and p["publish_date"].split(" ")[1] >= "14:00"
                ]
                if len(filtered_posts_info) < 10:
                    filtered_posts_info = posts_info[:10]  # 保留至少10个帖子
                logger.info(
                    f"过滤后：共 {len(filtered_posts_info)} 个当日发布的帖子（日期: {max_date}）"
                )
            else:
                logger.warning("无法识别发帖日期，使用全部帖子")
                filtered_posts_info = posts_info

            # 第二步：异步获取详情页
            logger.info("第二步：异步获取详情页...")
            detail_tasks = [
                _fetch_detail_page(client, post_info) for post_info in filtered_posts_info
            ]

            # 使用 asyncio.gather 并发执行所有详情页请求
            results = await asyncio.gather(*detail_tasks, return_exceptions=True)

            # 过滤掉异常和 None 结果
            valid_posts = [p for p in results if isinstance(p, TgbPost)]

            logger.info(
                f"爬虫完成！成功获取 {len(valid_posts)} 个帖子"
                f"（失败 {len(filtered_posts_info) - len(valid_posts)} 个）"
            )
            return valid_posts

        except Exception as e:
            logger.exception(f"爬虫执行出错: {e}")
            return []
