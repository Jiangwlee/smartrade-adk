"""
全局异常处理器

提供统一的异常处理机制，确保所有异常都返回标准的错误响应格式
"""

import logging
import traceback
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .base import APIException
from backend.schemas.responses import ApiError, ErrorDetail
from .error_codes import ErrorCode
from ..config.settings import settings

# 配置日志
logger = logging.getLogger(__name__)


def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    处理 APIException 异常

    Args:
        request: FastAPI 请求对象
        exc: APIException 异常实例

    Returns:
        JSONResponse: 标准化的错误响应
    """
    # 根据HTTP状态码选择日志级别
    if exc.http_status < 500:
        # 4xx错误 - 客户端错误,记录为warning
        log_level = logger.warning
    else:
        # 5xx错误 - 服务器错误,记录为error
        log_level = logger.error

    log_level(
        f"API Exception: {exc.error_type} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "error_type": exc.error_type,
            "http_status": exc.http_status,
            "details": exc.details,
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )

    # 创建错误详情
    error_detail = ErrorDetail(
        type=exc.error_type,
        details=exc.details
    )

    # 创建错误响应
    error_response = ApiError(
        code=exc.error_code,
        message=exc.message,
        error=error_detail
    )

    return JSONResponse(
        status_code=exc.http_status,
        content=error_response.model_dump(),
        headers=getattr(exc, 'headers', None)
    )


def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    处理 Pydantic 验证错误

    Args:
        request: FastAPI 请求对象
        exc: ValidationError 异常实例

    Returns:
        JSONResponse: 标准化的验证错误响应
    """
    # 格式化验证错误
    field_errors = {}
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        field_errors[field_path] = [error["msg"]]

    # 记录验证错误日志
    logger.warning(
        f"Validation Error: {len(exc.errors())} field validation errors",
        extra={
            "field_errors": field_errors,
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )

    # 创建错误详情
    error_detail = ErrorDetail(
        type="ValidationError",
        details={"fields": field_errors}
    )

    # 创建错误响应
    error_response = ApiError(
        code=ErrorCode.VALIDATION_ERROR,
        message="请求参数验证失败",
        error=error_detail
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )


def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理 FastAPI RequestValidationError（请求体验证失败）

    Args:
        request: FastAPI 请求对象
        exc: RequestValidationError 异常实例

    Returns:
        JSONResponse: 标准化的请求验证错误响应
    """
    # 格式化验证错误
    field_errors = {}
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        if field_path not in field_errors:
            field_errors[field_path] = []
        field_errors[field_path].append(error["msg"])

    # 记录验证错误日志
    logger.warning(
        f"Request Validation Error: {len(exc.errors())} field validation errors",
        extra={
            "field_errors": field_errors,
            "path": str(request.url.path),
            "method": request.method,
            "validation_errors": exc.errors()
        }
    )

    # 创建错误详情
    error_detail = ErrorDetail(
        type="RequestValidationError",
        details={
            "fields": field_errors,
            "validation_errors": exc.errors()
        }
    )

    # 创建错误响应
    error_response = ApiError(
        code=ErrorCode.VALIDATION_ERROR,
        message="请求参数验证失败",
        error=error_detail
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )


def response_validation_exception_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
    """
    处理 FastAPI ResponseValidationError（响应验证失败）

    Args:
        request: FastAPI 请求对象
        exc: ResponseValidationError 异常实例

    Returns:
        JSONResponse: 标准化的响应验证错误响应
    """
    # 记录响应验证错误日志（这种情况比较严重，通常表示代码问题）
    logger.error(
        f"Response Validation Error: {len(exc.errors())} validation errors in response",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "validation_errors": exc.errors()  # 只在日志中记录详细信息
        },
        exc_info=True
    )

    # 生产环境不返回详细错误信息
    if settings.debug:
        # 开发环境：返回详细错误信息
        error_detail = ErrorDetail(
            type="ResponseValidationError",
            details={"validation_errors": exc.errors()}
        )
        message = "服务器内部错误：响应格式验证失败"
    else:
        # 生产环境：隐藏详细错误信息
        error_detail = ErrorDetail(
            type="ResponseValidationError",
            details={}  # 生产环境隐藏详情
        )
        message = "服务器内部错误"

    # 创建错误响应
    error_response = ApiError(
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message=message,
        error=error_detail
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    处理 FastAPI HTTPException

    Args:
        request: FastAPI 请求对象
        exc: HTTPException 异常实例

    Returns:
        JSONResponse: 标准化的HTTP错误响应
    """
    # 映射HTTP状态码到错误码
    error_code_mapping = {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        413: ErrorCode.REQUEST_TOO_LARGE,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    error_code = error_code_mapping.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
    error_type = f"HTTP{exc.status_code}"

    # 记录HTTP错误日志
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "error_code": error_code,
            "error_type": error_type,
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )

    # 创建错误详情
    error_detail = ErrorDetail(
        type=error_type,
        details={"status_code": exc.status_code, "detail": exc.detail}
    )

    # 创建错误响应
    error_response = ApiError(
        code=error_code,
        message=str(exc.detail),
        error=error_detail
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的通用异常

    Args:
        request: FastAPI 请求对象
        exc: 通用异常实例

    Returns:
        JSONResponse: 标准化的服务器错误响应
    """
    # 记录详细的错误信息（包括堆栈跟踪）
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        },
        exc_info=True
    )

    # 在开发环境中，返回详细的错误信息
    import os
    is_development = os.getenv("ENVIRONMENT", "development") == "development"

    if is_development:
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc()
        }
    else:
        details = None  # 生产环境不暴露内部错误详情

    # 创建错误详情
    error_detail = ErrorDetail(
        type="InternalServerError",
        details=details
    )

    # 创建错误响应
    error_response = ApiError(
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="服务器内部错误",
        error=error_detail
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理 Starlette HTTPException

    Args:
        request: FastAPI 请求对象
        exc: StarletteHTTPException 异常实例

    Returns:
        JSONResponse: 标准化的HTTP错误响应
    """
    # 转换为 FastAPI HTTPException 处理
    fastapi_exc = HTTPException(
        status_code=exc.status_code,
        detail=exc.detail
    )
    return http_exception_handler(request, fastapi_exc)


def register_exception_handlers(app) -> None:
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    # 注册自定义 APIException 处理器
    app.add_exception_handler(APIException, api_exception_handler)

    # 注册 FastAPI 验证错误处理器（重要：这些是 FastAPI 实际使用的）
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ResponseValidationError, response_validation_exception_handler)

    # 注册 Pydantic 验证错误处理器（保留作为后备）
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # 注册 FastAPI HTTPException 处理器
    app.add_exception_handler(HTTPException, http_exception_handler)

    # 注册 Starlette HTTPException 处理器
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)

    # 注册通用异常处理器（必须是最后一个）
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("All exception handlers registered successfully")


def get_error_response(
    error_code: ErrorCode,
    message: str,
    error_type: str = None,
    details: Dict[str, Any] = None,
    http_status: int = None
) -> ApiError:
    """
    创建标准化的错误响应

    Args:
        error_code: 错误码
        message: 错误消息
        error_type: 错误类型 (可选)
        details: 错误详情 (可选)
        http_status: HTTP状态码 (可选)

    Returns:
        ApiError: 标准化的错误响应
    """
    if error_type is None:
        error_type = error_code.name.replace("_", " ").title()

    error_detail = ErrorDetail(
        type=error_type,
        details=details
    )

    return ApiError(
        code=error_code,
        message=message,
        error=error_detail
    )