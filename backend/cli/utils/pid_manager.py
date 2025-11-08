"""PID 文件管理工具模块

提供进程 PID 的读写、清理功能，用于管理 web server 进程。
"""
import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# PID 文件存储目录
PID_DIR = Path.home() / ".swkj" / "pids"


def _ensure_pid_dir() -> None:
    """确保 PID 目录存在"""
    PID_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"PID 目录已确保存在: {PID_DIR}")


def get_pid_file_path(server_name: str) -> Path:
    """获取指定服务器的 PID 文件路径

    Args:
        server_name: 服务器名称 (swkj, adk, ango)

    Returns:
        PID 文件的完整路径
    """
    return PID_DIR / f"{server_name}.pid"


def write_pid(server_name: str, pid: int) -> None:
    """将进程 PID 写入文件

    Args:
        server_name: 服务器名称 (swkj, adk, ango)
        pid: 进程 PID

    Raises:
        OSError: 写入文件失败
    """
    _ensure_pid_dir()
    pid_file = get_pid_file_path(server_name)

    try:
        pid_file.write_text(str(pid))
        logger.info(f"PID 文件已写入: {pid_file} (PID={pid})")
    except OSError as e:
        logger.error(f"写入 PID 文件失败 {pid_file}: {e}")
        raise


def read_pid(server_name: str) -> Optional[int]:
    """读取指定服务器的 PID

    Args:
        server_name: 服务器名称 (swkj, adk, ango)

    Returns:
        进程 PID，如果文件不存在或读取失败则返回 None
    """
    pid_file = get_pid_file_path(server_name)

    if not pid_file.exists():
        logger.debug(f"PID 文件不存在: {pid_file}")
        return None

    try:
        pid_str = pid_file.read_text().strip()
        pid = int(pid_str)
        logger.debug(f"读取 PID: {server_name} -> {pid}")
        return pid
    except (ValueError, OSError) as e:
        logger.warning(f"读取 PID 文件失败 {pid_file}: {e}")
        return None


def read_pids(server_name: Optional[str] = None) -> Dict[str, int]:
    """读取 PID 文件，返回服务器名和 PID 的映射

    Args:
        server_name: 可选，指定服务器名称。如果为 None，读取所有 PID 文件

    Returns:
        字典，键为服务器名称，值为 PID
    """
    if not PID_DIR.exists():
        logger.debug("PID 目录不存在，返回空字典")
        return {}

    result = {}

    if server_name:
        # 只读取指定服务器的 PID
        pid = read_pid(server_name)
        if pid is not None:
            result[server_name] = pid
    else:
        # 读取所有 .pid 文件
        for pid_file in PID_DIR.glob("*.pid"):
            name = pid_file.stem
            pid = read_pid(name)
            if pid is not None:
                result[name] = pid

    logger.debug(f"读取 PID 映射: {result}")
    return result


def cleanup_pid(server_name: str) -> bool:
    """删除 PID 文件

    Args:
        server_name: 服务器名称 (swkj, adk, ango)

    Returns:
        是否成功删除文件
    """
    pid_file = get_pid_file_path(server_name)

    if not pid_file.exists():
        logger.debug(f"PID 文件不存在，无需删除: {pid_file}")
        return True

    try:
        pid_file.unlink()
        logger.info(f"PID 文件已删除: {pid_file}")
        return True
    except OSError as e:
        logger.error(f"删除 PID 文件失败 {pid_file}: {e}")
        return False


def cleanup_all_pids() -> None:
    """删除所有 PID 文件"""
    if not PID_DIR.exists():
        logger.debug("PID 目录不存在，无需清理")
        return

    for pid_file in PID_DIR.glob("*.pid"):
        server_name = pid_file.stem
        cleanup_pid(server_name)

    logger.info("所有 PID 文件已清理")
