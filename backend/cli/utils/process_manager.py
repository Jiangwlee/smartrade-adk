"""进程管理工具模块

提供进程启动、停止、端口检查等功能。

注意：本模块依赖 Unix-like 系统命令（lsof, ps, kill），仅支持 macOS 和 Linux 系统。
Windows 系统不支持。
"""
import os
import signal
import subprocess
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def check_port_available(port: int) -> bool:
    """检查端口是否可用

    Args:
        port: 端口号

    Returns:
        True 表示端口可用，False 表示端口被占用
    """
    try:
        # 使用 lsof 检查端口占用
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # 如果有输出，说明端口被占用
        is_occupied = bool(result.stdout.strip())
        if is_occupied:
            logger.warning(f"端口 {port} 已被占用")
            return False
        else:
            logger.debug(f"端口 {port} 可用")
            return True
    except subprocess.TimeoutExpired:
        logger.error(f"检查端口 {port} 超时")
        return False
    except FileNotFoundError:
        # lsof 命令不存在，假设端口可用
        logger.warning("lsof 命令不存在，无法检查端口占用")
        return True


def get_process_by_port(port: int) -> Optional[int]:
    """通过端口获取占用该端口的进程 PID

    Args:
        port: 端口号

    Returns:
        进程 PID，如果没有进程占用则返回 None
    """
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        pid_str = result.stdout.strip()
        if pid_str:
            pid = int(pid_str.split('\n')[0])  # 可能有多个进程，取第一个
            logger.debug(f"端口 {port} 被进程 {pid} 占用")
            return pid
        return None
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
        logger.warning(f"获取端口 {port} 的进程失败: {e}")
        return None


def is_process_running(pid: int) -> bool:
    """检查进程是否正在运行

    Args:
        pid: 进程 PID

    Returns:
        True 表示进程正在运行，False 表示进程不存在
    """
    try:
        # 使用 ps 检查进程是否存在
        result = subprocess.run(
            ["ps", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        is_running = result.returncode == 0
        logger.debug(f"进程 {pid} 运行状态: {is_running}")
        return is_running
    except subprocess.TimeoutExpired:
        logger.error(f"检查进程 {pid} 超时")
        return False


def kill_process(pid: int, timeout: int = 10) -> bool:
    """优雅地关闭进程

    首先发送 SIGTERM 信号，如果超时后进程仍在运行，则发送 SIGKILL 强制终止。

    Args:
        pid: 进程 PID
        timeout: 等待进程退出的超时时间（秒）

    Returns:
        True 表示成功关闭进程，False 表示失败
    """
    if not is_process_running(pid):
        logger.info(f"进程 {pid} 不存在或已退出")
        return True

    try:
        # 发送 SIGTERM 信号
        logger.info(f"发送 SIGTERM 信号到进程 {pid}")
        os.kill(pid, signal.SIGTERM)

        # 等待进程退出
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not is_process_running(pid):
                logger.info(f"进程 {pid} 已优雅退出")
                return True
            time.sleep(0.5)

        # 超时后强制终止
        logger.warning(f"进程 {pid} 未在 {timeout} 秒内退出，发送 SIGKILL 强制终止")
        os.kill(pid, signal.SIGKILL)

        # 再次等待确认
        time.sleep(1)
        if not is_process_running(pid):
            logger.info(f"进程 {pid} 已强制终止")
            return True
        else:
            logger.error(f"无法终止进程 {pid}")
            return False

    except ProcessLookupError:
        logger.info(f"进程 {pid} 在终止过程中已退出")
        return True
    except PermissionError:
        logger.error(f"没有权限终止进程 {pid}")
        return False
    except Exception as e:
        logger.error(f"终止进程 {pid} 时发生错误: {e}")
        return False


def verify_process_and_port(pid: int, expected_port: int) -> bool:
    """验证进程是否存在且监听指定端口

    Args:
        pid: 进程 PID
        expected_port: 期望的监听端口

    Returns:
        True 表示进程存在且监听指定端口，False 表示不匹配
    """
    if not is_process_running(pid):
        logger.warning(f"进程 {pid} 不存在")
        return False

    port_pid = get_process_by_port(expected_port)
    if port_pid == pid:
        logger.debug(f"进程 {pid} 正在监听端口 {expected_port}")
        return True
    else:
        logger.warning(
            f"进程 {pid} 未监听端口 {expected_port} "
            f"(端口被进程 {port_pid} 占用)" if port_pid else f"(端口 {expected_port} 未被占用)"
        )
        return False
