#!/usr/bin/env python3
"""Web Server 启动脚本

提供统一的命令行接口来启动和停止不同的 web server。
"""
import os
import sys
import time
import multiprocessing
from pathlib import Path
from typing import Optional

import click
import uvicorn
from uvicorn.supervisors import ChangeReload
from dotenv import load_dotenv
import litellm

from .utils.pid_manager import write_pid, read_pids, cleanup_pid
from .utils.process_manager import check_port_available, kill_process, verify_process_and_port
from ..config.logging import setup_logging, get_logger

# 添加 backend 目录到 Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# 加载环境变量
load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")

if os.environ.get("LITELLM_DEBUG", "false").lower() == "true":
    litellm._turn_on_debug()


AGENT_DIR = "backend/agents/"

# 服务器配置映射
SERVER_CONFIG = {
    "smartrade": {"port": 8000, "name": "Smartrade Web Server"},
    # "adk": {"port": 8001, "name": "ADK Web Server"},
}

setup_logging()
logger = get_logger(__name__)

def start_single_server(
    server_name: str,
    host: str,
    allow_origins: tuple[str, ...],
    session_service_uri: Optional[str],
    artifact_service_uri: Optional[str],
    memory_service_uri: Optional[str],
    eval_storage_uri: Optional[str],
    trace_to_cloud: bool,
    reload: bool,
):
    """启动单个 server

    Args:
        server_name: 服务器名称 (swkj, adk, ango)
        其他参数: 共享配置参数
    """
    if server_name not in SERVER_CONFIG:
        click.secho(f"❌ 未知的服务器名称: {server_name}", fg="red")
        click.secho(f"   可用选项: {', '.join(SERVER_CONFIG.keys())}", fg="yellow")
        sys.exit(1)

    config = SERVER_CONFIG[server_name]
    port = config["port"]
    server_title = config["name"]

    # 检查端口是否可用
    if not check_port_available(port):
        click.secho(f"❌ 端口 {port} 已被占用，无法启动 {server_title}", fg="red")
        sys.exit(1)

    # 准备参数
    allow_origins_list = list(allow_origins) if allow_origins else None

    # 设置应用配置（用于 app_factory 模块）
    from .app_factory import set_app_config

    set_app_config(
        server_name=server_name,
        agents_dir=AGENT_DIR,
        session_service_uri=session_service_uri,
        artifact_service_uri=artifact_service_uri,
        memory_service_uri=memory_service_uri,
        eval_storage_uri=eval_storage_uri,
        allow_origins=allow_origins_list,
    )

    # 记录当前进程 PID
    current_pid = os.getpid()
    write_pid(server_name, current_pid)
    

    # 显示启动信息
    click.secho(
        f"""
╔══════════════════════════════════════════════════════════════════╗
║ {server_title:<64} ║
║                                                                  ║
║ 访问地址: http://{host}:{port}{' ' * (47 - len(f'{host}:{port}'))} ║
║ PID: {current_pid:<59} ║
╚══════════════════════════════════════════════════════════════════╝
""",
        fg="green",
    )

    # 配置并启动 uvicorn
    # 使用工厂路径 "backend.cli.app_factory:get_app" 以支持 reload 功能
    config = uvicorn.Config(
        "backend.cli.app_factory:get_app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(Path(__file__).resolve().parents[1])] if reload else None,
        factory=True,
    )

    server = uvicorn.Server(config)

    try:
        if config.should_reload:
            sock = config.bind_socket()
            ChangeReload(config, target=server.run, sockets=[sock]).run()
        else:
            server.run()
    except KeyboardInterrupt:
        logger.info(f"{server_title} stopped by user")
    except Exception as e:
        logger.error(f"{server_title} error: {e}")
        sys.exit(1)
    finally:
        # 清理 PID 文件（仅当 PID 文件中的 PID 与当前进程匹配时）
        from .utils.pid_manager import read_pid
        stored_pid = read_pid(server_name)
        if stored_pid == current_pid:
            cleanup_pid(server_name)
        else:
            logger.debug(
                f"PID 文件中的 PID ({stored_pid}) 与当前进程 ({current_pid}) 不匹配，跳过清理"
            )


@click.group()
def cli():
    """Web Server 管理工具"""
    pass


@cli.command()
@click.option(
    "--servers",
    default="swkj",
    help="要启动的服务器 (swkj|adk|ango)",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="主机地址",
)
@click.option(
    "--allow-origins",
    multiple=True,
    default=["http://localhost:3000", "http://localhost:4200", "http://localhost:7777"],
    help="允许的 CORS 来源",
)
@click.option(
    "--session-service-uri",
    help="会话服务 URI",
)
@click.option(
    "--artifact-service-uri",
    help="Artifact 服务 URI",
)
@click.option(
    "--memory-service-uri",
    help="内存服务 URI",
)
@click.option(
    "--eval-storage-uri",
    help="评估存储 URI",
)
@click.option(
    "--trace-to-cloud",
    is_flag=True,
    default=False,
    help="启用云追踪",
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="启用自动重载（开发模式）",
)
def start(
    servers: str,
    host: str,
    allow_origins: tuple[str, ...],
    session_service_uri: Optional[str],
    artifact_service_uri: Optional[str],
    memory_service_uri: Optional[str],
    eval_storage_uri: Optional[str],
    trace_to_cloud: bool,
    reload: bool,
):
    """启动 web server"""
    if servers == "all":
        # 启动所有服务器
        server_names = list(SERVER_CONFIG.keys())
        click.secho(f"🚀 启动所有服务器: {', '.join(server_names)}", fg="cyan")

        processes = []
        for server_name in server_names:
            # 创建独立进程
            process = multiprocessing.Process(
                target=start_single_server,
                args=(
                    server_name,
                    host,
                    allow_origins,
                    session_service_uri,
                    artifact_service_uri,
                    memory_service_uri,
                    eval_storage_uri,
                    trace_to_cloud,
                    reload,
                ),
            )
            process.start()
            processes.append(process)
            click.secho(f"✓ {SERVER_CONFIG[server_name]['name']} 进程已启动 (PID={process.pid})", fg="green")
            time.sleep(1)  # 避免端口冲突检测竞争

        click.secho("\n所有服务器已启动！按 Ctrl+C 停止所有服务器。\n", fg="green")

        try:
            # 等待所有进程
            for process in processes:
                process.join()
        except KeyboardInterrupt:
            click.secho("\n🛑 正在停止所有服务器...", fg="yellow")
            for process in processes:
                process.terminate()
            for process in processes:
                process.join()
            click.secho("✅ 所有服务器已停止", fg="green")
    else:
        # 启动单个服务器
        start_single_server(
            server_name=servers,
            host=host,
            allow_origins=allow_origins,
            session_service_uri=session_service_uri,
            artifact_service_uri=artifact_service_uri,
            memory_service_uri=memory_service_uri,
            eval_storage_uri=eval_storage_uri,
            trace_to_cloud=trace_to_cloud,
            reload=reload,
        )


@cli.command()
@click.option(
    "--servers",
    default="all",
    help="要停止的服务器 (all|smartrade)",
)

def stop(servers: str):
    """停止 web server"""
    # 读取所有或指定的 PID
    if servers == "all":
        pids = read_pids()
        if not pids:
            click.secho("ℹ️  没有运行中的服务器", fg="yellow")
            return
    else:
        if servers not in SERVER_CONFIG:
            click.secho(f"❌ 未知的服务器名称: {servers}", fg="red")
            click.secho(f"   可用选项: {', '.join(SERVER_CONFIG.keys())}", fg="yellow")
            sys.exit(1)

        pids = read_pids(servers)
        if not pids:
            click.secho(f"ℹ️  {SERVER_CONFIG[servers]['name']} 未运行", fg="yellow")
            return

    # 停止进程
    for server_name, pid in pids.items():
        config = SERVER_CONFIG.get(server_name)
        if not config:
            logger.warning(f"未知的服务器名称: {server_name}")
            cleanup_pid(server_name)
            continue

        server_title = config["name"]
        port = config["port"]

        # 验证进程
        if verify_process_and_port(pid, port):
            click.secho(f"🛑 正在停止 {server_title} (PID={pid})...", fg="yellow")

            if kill_process(pid):
                click.secho(f"✅ {server_title} 已停止", fg="green")
                cleanup_pid(server_name)
            else:
                click.secho(f"❌ 无法停止 {server_title}", fg="red")
        else:
            click.secho(
                f"ℹ️  {server_title} 的进程 {pid} 不存在或未监听端口 {port}，清理 PID 文件",
                fg="yellow",
            )
            cleanup_pid(server_name)


if __name__ == "__main__":
    cli()
