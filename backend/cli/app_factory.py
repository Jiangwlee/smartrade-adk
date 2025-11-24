"""应用工厂 - 用于 Uvicorn reload 支持

这个模块负责创建 FastAPI 应用实例。Uvicorn 的 reload 功能
只能与模块级别的应用对象配合工作，因此将应用创建逻辑
单独提取到这个模块中。
"""
import json
import os
from typing import Any, Optional

APP_CONFIG_ENV_KEY = "SMARTRADE_WEB_APP_CONFIG"

# 通过 env + 内存缓存共享配置，支持 uvicorn reload 多进程
_app_config: Optional[dict[str, Any]] = None


def _ensure_app_config() -> dict[str, Any]:
    """懒加载配置，优先使用内存，没有则回落到环境变量"""
    global _app_config

    if _app_config is not None:
        return _app_config

    raw_config = os.environ.get(APP_CONFIG_ENV_KEY)
    if raw_config:
        try:
            _app_config = json.loads(raw_config)
        except json.JSONDecodeError:
            _app_config = {}
    else:
        _app_config = {}

    return _app_config


def set_app_config(
    server_name: str,
    agents_dir: str,
    session_service_uri: Optional[str],
    artifact_service_uri: Optional[str],
    memory_service_uri: Optional[str],
    eval_storage_uri: Optional[str],
    allow_origins: Optional[list[str]],
):
    """设置应用配置，并持久化到 env 供 uvicorn reload 子进程读取"""
    global _app_config

    normalized_config = {
        "server_name": server_name,
        "agents_dir": agents_dir,
        "session_service_uri": session_service_uri,
        "artifact_service_uri": artifact_service_uri,
        "memory_service_uri": memory_service_uri,
        "eval_storage_uri": eval_storage_uri,
        "allow_origins": list(allow_origins) if allow_origins else None,
    }

    _app_config = normalized_config
    os.environ[APP_CONFIG_ENV_KEY] = json.dumps(normalized_config)


def get_app():
    """应用工厂 - 模块级别可调用对象，支持 Uvicorn reload"""
    config = _ensure_app_config()
    server_name = config.get("server_name", "smartrade")

    if server_name == "smartrade":
        from .smartrade_web_server import get_smartrade_web_app

        return get_smartrade_web_app(
            agents_dir=config.get("agents_dir", "backend/agents/"),
            session_service_uri=config.get("session_service_uri"),
            artifact_service_uri=config.get("artifact_service_uri"),
            memory_service_uri=config.get("memory_service_uri"),
            eval_storage_uri=config.get("eval_storage_uri"),
            allow_origins=config.get("allow_origins"),
        )
    else:
        raise ValueError(f"Unknown server: {server_name}")
