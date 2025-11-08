"""
异常体系基类

提供统一的异常基类和通用异常
"""

from typing import Optional, Dict, Any
from fastapi import status

from .error_codes import ErrorCode


class APIException(Exception):
    """
    API 异常基类

    所有业务异常继承此类，提供统一的异常结构

    Attributes:
        error_code: 应用层错误码
        message: 错误消息
        http_status: HTTP 状态码
        error_type: 错误类型
        details: 错误详情
    """

    error_code: int = ErrorCode.BAD_REQUEST
    http_status: int = status.HTTP_400_BAD_REQUEST
    error_type: str = "BadRequest"

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            details: 错误详情，可选
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            Dict[str, Any]: 异常信息字典
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "http_status": self.http_status,
            "error_type": self.error_type,
            "details": self.details
        }


# ============ 通用错误 (400xx) ============

class BadRequestException(APIException):
    """400 Bad Request - 请求参数错误"""
    error_code = ErrorCode.BAD_REQUEST
    http_status = status.HTTP_400_BAD_REQUEST
    error_type = "BadRequest"


class InvalidFormatException(APIException):
    """400 Bad Request - 请求格式错误"""
    error_code = ErrorCode.INVALID_FORMAT
    http_status = status.HTTP_400_BAD_REQUEST
    error_type = "InvalidFormat"


class InvalidDataException(APIException):
    """400 Bad Request - 请求数据无效"""
    error_code = ErrorCode.INVALID_DATA
    http_status = status.HTTP_400_BAD_REQUEST
    error_type = "InvalidData"


class MissingParameterException(APIException):
    """400 Bad Request - 缺少必需参数"""
    error_code = ErrorCode.MISSING_PARAMETER
    http_status = status.HTTP_400_BAD_REQUEST
    error_type = "MissingParameter"


class InvalidParameterException(APIException):
    """400 Bad Request - 无效参数值"""
    error_code = ErrorCode.INVALID_PARAMETER
    http_status = status.HTTP_400_BAD_REQUEST
    error_type = "InvalidParameter"


class RateLimitExceededException(APIException):
    """429 Too Many Requests - 请求频率超限"""
    error_code = ErrorCode.RATE_LIMIT_EXCEEDED
    http_status = status.HTTP_429_TOO_MANY_REQUESTS
    error_type = "RateLimitExceeded"


class MaintenanceModeException(APIException):
    """503 Service Unavailable - 系统维护中"""
    error_code = ErrorCode.MAINTENANCE_MODE
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    error_type = "MaintenanceMode"


class InvalidOperationException(APIException):
    """400 Bad Request - 无效操作"""
    error_code = ErrorCode.INVALID_OPERATION
    http_status = status.HTTP_400_BAD_REQUEST
    error_type = "InvalidOperation"