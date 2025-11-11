"""
全局日志配置模块

提供统一的日志配置，支持：
- 终端输出（彩色格式）
- 文件输出（按日期轮转）
- JSON 和 TEXT 两种格式
- 根据环境变量自动配置
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from .settings import settings


class ColoredFormatter(logging.Formatter):
    """带颜色的终端日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }

    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # 格式化消息
        result = super().format(record)

        # 重置 levelname（避免影响其他 handler）
        record.levelname = levelname

        return result


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    配置全局日志系统

    Args:
        log_dir: 日志文件目录，默认为项目根目录/log
        log_level: 日志级别，默认从 settings 读取
        log_format: 日志格式 (json/text)，默认从 settings 读取
        enable_console: 是否启用终端输出
        enable_file: 是否启用文件输出
    """
    # 使用默认值
    if log_dir is None:
        # 项目根目录 = backend 的父目录
        project_root = Path(__file__).resolve().parents[2]
        log_dir = project_root / "log"

    if log_level is None:
        log_level = settings.log_level

    if log_format is None:
        log_format = settings.log_format

    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)

    # 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # 清除已有的 handlers（避免重复）
    root_logger.handlers.clear()

    # 1. 终端 Handler（彩色输出）
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))

        if log_format == "json":
            console_formatter = JSONFormatter()
        else:
            # 终端使用彩色格式
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 2. 文件 Handler（按日期轮转）
    if enable_file:
        # 应用日志文件（所有级别）
        app_log_file = log_dir / "app.log"
        app_file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=app_log_file,
            when='midnight',      # 每天午夜轮转
            interval=1,           # 间隔1天
            backupCount=30,       # 保留30天
            encoding='utf-8',
        )
        app_file_handler.setLevel(getattr(logging, log_level))

        # 文件使用更详细的格式
        if log_format == "json":
            app_file_formatter = JSONFormatter()
        else:
            app_file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        app_file_handler.setFormatter(app_file_formatter)
        root_logger.addHandler(app_file_handler)

        # 错误日志文件（仅 ERROR 及以上）
        error_log_file = log_dir / "error.log"
        error_file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=error_log_file,
            when='midnight',
            interval=1,
            backupCount=90,       # 错误日志保留更久
            encoding='utf-8',
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(app_file_formatter)
        root_logger.addHandler(error_file_handler)

    # 3. 配置第三方库的日志级别（避免过度输出）
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # 减少访问日志
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)

    # 抑制ADK的App name mismatch警告（不影响功能）
    logging.getLogger("google_adk.google.adk.runners").setLevel(logging.ERROR)

    # 记录日志系统已初始化
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info(f"日志系统已初始化")
    logger.info(f"  - 日志级别: {log_level}")
    logger.info(f"  - 日志格式: {log_format}")
    logger.info(f"  - 终端输出: {'启用' if enable_console else '禁用'}")
    logger.info(f"  - 文件输出: {'启用' if enable_file else '禁用'}")
    if enable_file:
        logger.info(f"  - 日志目录: {log_dir}")
    logger.info("="*60)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        配置好的 logger 实例

    Example:
        >>> from backend.config.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello, world!")
    """
    return logging.getLogger(name)


# 快捷函数：在导入时自动初始化（可选）
def auto_setup_logging():
    """自动初始化日志系统（如果尚未初始化）"""
    root_logger = logging.getLogger()

    # 如果已经有 handlers，说明已经初始化过了
    if not root_logger.handlers:
        setup_logging()


# 导出
__all__ = [
    'setup_logging',
    'get_logger',
    'auto_setup_logging',
    'ColoredFormatter',
    'JSONFormatter',
]
