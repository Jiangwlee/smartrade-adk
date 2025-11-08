"""
统一响应 Schema

定义所有 API 响应的标准结构，确保前端处理逻辑一致
遵循 design.md v2.0 统一封装方案
"""

from typing import Generic, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# 泛型类型变量
T = TypeVar('T')


# ============ 成功响应 Schema ============

class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应封装

    所有成功响应使用此结构

    Examples:
        # 简单数据
        ApiResponse[User](
            code=200,
            message="获取用户成功",
            data=user
        )

        # 列表数据
        ApiResponse[UserListData](
            code=200,
            message="获取列表成功",
            data={"items": [...], "pagination": {...}}
        )
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

    code: int = Field(
        description="应用层状态码,通常与 HTTP status 一致"
    )
    message: str = Field(
        description="响应消息,前端可直接展示"
    )
    data: T = Field(
        description="业务数据"
    )


# ============ 错误响应 Schema ============

class ErrorDetail(BaseModel):
    """
    错误详情

    提供结构化的错误信息
    """
    type: str = Field(
        description="错误类型 (如 ValidationError, UserNotFound)"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="额外的错误详情"
    )


class ApiError(BaseModel):
    """
    统一错误响应

    所有错误响应使用此结构

    Examples:
        ApiError(
            code=40401,
            message="用户不存在",
            error=ErrorDetail(
                type="UserNotFound",
                details={"user_id": "123"}
            )
        )
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

    code: int = Field(
        description="应用层错误码"
    )
    message: str = Field(
        description="错误消息,前端可直接展示"
    )
    error: Optional[ErrorDetail] = Field(
        None,
        description="错误详情 (可选)"
    )


# ============ 通用数据容器 Schema ============

class PaginationMeta(BaseModel):
    """
    分页元数据
    """
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, le=100, description="每页大小")
    total: int = Field(..., ge=0, description="总记录数")
    pages: int = Field(..., ge=0, description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

    @classmethod
    def create(cls, page: int, size: int, total: int) -> "PaginationMeta":
        """创建分页元数据"""
        pages = (total + size - 1) // size if total > 0 else 0
        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class PagedData(BaseModel, Generic[T]):
    """
    分页数据容器

    用于列表响应的 data 字段

    Examples:
        ApiResponse[PagedData[User]](
            code=200,
            message="获取用户列表成功",
            data=PagedData(
                items=[...],
                pagination=PaginationMeta.create(1, 20, 100)
            )
        )
    """
    items: List[T] = Field(..., description="数据项列表")
    pagination: PaginationMeta = Field(..., description="分页信息")


class MessageData(BaseModel):
    """
    消息数据容器

    用于操作端点返回简单消息
    """
    message: str = Field(..., description="消息内容")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="附加信息"
    )


class BulkOperationData(BaseModel):
    """
    批量操作结果容器
    """
    total: int = Field(..., ge=0, description="总操作数")
    success: int = Field(..., ge=0, description="成功数")
    failed: int = Field(..., ge=0, description="失败数")
    success_ids: List[str] = Field(
        default_factory=list,
        description="成功的ID列表"
    )
    failed_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="失败的项目(包含ID和错误信息)"
    )


class TaskData(BaseModel):
    """
    异步任务结果容器
    """
    task_id: str = Field(..., description="任务ID")
    status: str = Field(
        ...,
        description="任务状态: pending/running/completed/failed"
    )
    message: str = Field(..., description="任务状态说明")
    result: Optional[Any] = Field(None, description="任务结果(完成后)")
    error_message: Optional[str] = Field(
        None,
        description="错误信息(失败时)"
    )


class HealthCheckData(BaseModel):
    """
    健康检查数据容器
    """
    status: str = Field(..., description="健康状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: Optional[str] = Field(None, description="应用版本")
    components: Optional[Dict[str, Any]] = Field(None, description="组件状态")


class FileUploadData(BaseModel):
    """
    文件上传数据容器
    """
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件类型")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")


# ============ 验证错误详情 Schema ============

class ValidationErrorField(BaseModel):
    """
    字段验证错误详情
    """
    field: str = Field(..., description="字段名")
    messages: List[str] = Field(..., description="错误消息列表")