from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import Optional, Iterable, List
from fastapi.middleware.cors import CORSMiddleware
from logging import getLogger

from ..api.endpoint import AdkFastAPIEndpoint
from ..exceptions.exception_handlers import register_exception_handlers

logger = getLogger(__name__)

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """应用生命周期管理"""
    pass


def get_smartrade_web_app(
    *,
    agent_dir: str,
    allow_origins: Optional[List[str]] = None,
) -> FastAPI:
    """创建 Smartrade Web Server 的 FastAPI 应用

    Args:
        allow_origins: 允许的 CORS 来源列表

    Returns:
        FastAPI 应用实例
    """

    app = FastAPI(
        title="Smartrade Web Server",
        description="A股交易大师",
        version="1.0.0",
        lifespan=app_lifespan  # 生命周期管理
    )

    # 配置 CORS
    if allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS enabled for origins: {allow_origins}")

    # 注册全局异常处理器
    register_exception_handlers(app)
    logger.info("Global exception handlers registered")

    # 挂载应用管理路由
    adk_endpoint = AdkFastAPIEndpoint(agent_dir)
    adk_endpoint.add_adk_fastapi_endpoint(app)

    logger.info("Smartrade Web Server initialized successfully")

    return app