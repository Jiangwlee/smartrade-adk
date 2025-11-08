from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import Optional, Mapping, List, Any
from fastapi.middleware.cors import CORSMiddleware
from logging import getLogger

from ..api.endpoint import AdkFastAPIEndpoint
from ..exceptions.exception_handlers import register_exception_handlers

logger = getLogger(__name__)

# @asynccontextmanager
# async def app_lifespan(app: FastAPI):
#     """应用生命周期管理"""
#     pass


def get_smartrade_web_app(
    *,
    agents_dir: str,
    allow_origins: Optional[List[str]] = None,
    session_service_uri: Optional[str] = None,
    session_db_kwargs: Optional[Mapping[str, Any]] = None,
    artifact_service_uri: Optional[str] = None,
    memory_service_uri: Optional[str] = None,
    eval_storage_uri: Optional[str] = None,
    url_prefix: Optional[str] = None,
    extra_plugins: Optional[list[str]] = None,
    logo_text: Optional[str] = None,
    logo_image_url: Optional[str] = None,
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
        # lifespan=app_lifespan  # 生命周期管理
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
    adk_endpoint = AdkFastAPIEndpoint()
    adk_endpoint.create_adk_web_server(
        agents_dir=agents_dir,
        session_service_uri=session_service_uri,
        session_db_kwargs=session_db_kwargs,
        artifact_service_uri=artifact_service_uri,
        memory_service_uri=memory_service_uri,
        eval_storage_uri=eval_storage_uri,
        url_prefix=url_prefix,
        extra_plugins=extra_plugins,
        logo_text=logo_text,
        logo_image_url=logo_image_url,
    )
    adk_endpoint.add_adk_fastapi_endpoint(app)

    logger.info("Smartrade Web Server initialized successfully")

    return app