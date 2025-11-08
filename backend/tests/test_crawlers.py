"""测试所有爬虫功能

简单的测试脚本，用于验证重构后的爬虫是否正常工作

PYTHONPATH=/Users/mindora/Workspace/projects/smartrade-adk/backend python crawlers/test_crawlers.py
"""

import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def test_ths_hot_board():
    """测试同花顺热门板块爬虫"""
    logger.info("=" * 60)
    logger.info("测试同花顺热门板块爬虫")
    logger.info("=" * 60)

    try:
        from crawlers.tonghuashun.ths_hot_board import crawl

        # 使用今天的日期
        today = datetime.now().strftime("%Y%m%d")
        report = await crawl(date='20251107', delta=1)

        logger.info(f"✅ 同花顺爬虫测试成功")
        logger.info(f"报告长度: {len(report)} 字符")
        logger.info(f"报告预览（前500字符）:\n{report[:500]}")

    except Exception as e:
        logger.error(f"❌ 同花顺爬虫测试失败: {e}", exc_info=True)


async def test_tgb_jinghua():
    """测试淘股吧精华帖爬虫"""
    logger.info("=" * 60)
    logger.info("测试淘股吧精华帖爬虫")
    logger.info("=" * 60)

    try:
        from crawlers.taoguba.tgb_jinghua import crawl

        posts = await crawl()

        logger.info(f"✅ 淘股吧爬虫测试成功")
        logger.info(f"获取到 {len(posts)} 个帖子")
        if posts:
            logger.info(f"第一个帖子: {posts[0].title} - {posts[0].author}")

    except Exception as e:
        logger.error(f"❌ 淘股吧爬虫测试失败: {e}", exc_info=True)


async def test_jrj_hangqing():
    """测试金融界行情爬虫"""
    logger.info("=" * 60)
    logger.info("测试金融界行情爬虫")
    logger.info("=" * 60)

    try:
        from crawlers.jinrongjie.jrj import HangQingType, crawl

        # 测试获取日线数据
        data = await crawl(code="000001", name="平安银行", hangqing_type=HangQingType.DAY)

        logger.info(f"✅ 金融界爬虫测试成功")
        logger.info(f"获取到 {len(data)} 条K线数据")
        if data:
            logger.info(
                f"最新数据: 时间={data[0].time}, "
                f"收盘价={data[0].close}, "
                f"成交量={data[0].volume}"
            )

    except Exception as e:
        logger.error(f"❌ 金融界爬虫测试失败: {e}", exc_info=True)


async def main():
    """运行所有测试"""
    logger.info("\n开始测试所有爬虫...")
    logger.info("=" * 60)

    # 运行所有测试
    await test_ths_hot_board()
    print("\n")

    await test_tgb_jinghua()
    print("\n")

    await test_jrj_hangqing()
    print("\n")

    logger.info("=" * 60)
    logger.info("所有测试完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
