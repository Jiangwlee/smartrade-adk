"""
错误码枚举

定义所有应用层错误码，采用5位数字格式: XYZNN
- X: 错误级别 (4: 客户端错误, 5: 服务器错误)
- YZ: 错误类别 (00-99)
- NN: 具体错误 (00-99)

参考: design.md 第3节 错误码体系
"""

from enum import IntEnum


class ErrorCode(IntEnum):
    """
    应用层错误码

    错误码格式: XYZNN
    - X: 错误级别 (4: 客户端错误, 5: 服务器错误)
    - YZ: 错误类别
        - 40x: 通用客户端错误
        - 41x: 认证相关
        - 42x: 验证相关
        - 43x: 权限相关
        - 44x: 资源相关
        - 45x: 业务逻辑相关
        - 50x: 通用服务器错误
        - 51x: 数据库相关
        - 52x: 外部服务相关
    - NN: 具体错误 (00-99)
    """

    # ============ 通用错误 (400xx) ============

    BAD_REQUEST = 40000  # 请求参数错误
    INVALID_FORMAT = 40001  # 请求格式错误 (如JSON格式错误)
    INVALID_DATA = 40002  # 请求数据无效 (数据类型不匹配)
    MISSING_PARAMETER = 40003  # 缺少必需参数
    INVALID_PARAMETER = 40004  # 无效参数值
    UNSUPPORTED_MEDIA_TYPE = 40005  # 不支持的媒体类型
    REQUEST_TOO_LARGE = 40006  # 请求体过大
    RATE_LIMIT_EXCEEDED = 40007  # 请求频率超限

    # ============ 认证错误 (41xxx) ============

    UNAUTHORIZED = 41000  # 未认证 (缺少token)
    INVALID_TOKEN = 41001  # token无效 (格式错误)
    TOKEN_EXPIRED = 41002  # token过期
    AUTH_FAILED = 41003  # 认证失败 (用户名或密码错误)
    INVALID_CREDENTIALS = 41004  # 凭据无效
    ACCOUNT_LOCKED = 41005  # 账户被锁定
    ACCOUNT_SUSPENDED = 41006  # 账户被暂停
    TOKEN_REVOKED = 41007  # token已被撤销

    # ============ 验证错误 (42xxx) ============

    VALIDATION_ERROR = 42200  # 验证失败 (通用)
    INVALID_FORMAT_FIELD = 42201  # 格式错误 (如邮箱格式)
    INVALID_LENGTH = 42202  # 长度错误 (太短或太长)
    INVALID_RANGE = 42203  # 范围错误 (值超出范围)
    REQUIRED_FIELD_MISSING = 42204  # 必填字段缺失
    INVALID_EMAIL = 42205  # 邮箱格式无效
    INVALID_PHONE = 42206  # 电话格式无效
    INVALID_URL = 42207  # URL格式无效
    INVALID_DATE = 42208  # 日期格式无效
    WEAK_PASSWORD = 42209  # 密码强度不够

    # ============ 权限错误 (43xxx) ============

    FORBIDDEN = 43000  # 权限不足 (通用)
    ACCESS_DENIED = 43001  # 访问被拒绝 (IP黑名单等)
    ACCOUNT_DISABLED = 43002  # 账号被禁用
    INSUFFICIENT_PERMISSIONS = 43003  # 权限不足，缺少所需权限
    ROLE_REQUIRED = 43004  # 需要特定角色
    PREMIUM_REQUIRED = 43005  # 需要高级权限
    ADMIN_REQUIRED = 43006  # 需要管理员权限

    # ============ 资源错误 (44xxx) ============

    RESOURCE_NOT_FOUND = 44000  # 资源不存在 (通用)
    USER_NOT_FOUND = 44001  # 用户不存在
    ROLE_NOT_FOUND = 44002  # 角色不存在
    APPLICATION_NOT_FOUND = 44003  # 应用不存在
    INVITE_CODE_NOT_FOUND = 44004  # 邀请码不存在
    SESSION_NOT_FOUND = 44005  # 会话不存在
    FILE_NOT_FOUND = 44006  # 文件不存在
    CONFIG_NOT_FOUND = 44007  # 配置不存在
    TASK_NOT_FOUND = 44008  # 任务不存在

    # ============ 业务逻辑错误 (45xxx) ============

    USERNAME_ALREADY_EXISTS = 45001  # 用户名已存在
    EMAIL_ALREADY_EXISTS = 45002  # 邮箱已存在
    RESOURCE_ALREADY_EXISTS = 45003  # 资源已存在 (通用)
    INVITE_CODE_EXPIRED = 45004  # 邀请码已过期
    INVITE_CODE_USED_UP = 45005  # 邀请码已用完
    INVALID_OPERATION = 45006  # 无效操作
    RESOURCE_CONFLICT = 45007  # 资源冲突
    DEPENDENCY_ERROR = 45008  # 依赖错误 (如删除有依赖的资源)
    QUOTA_EXCEEDED = 45009  # 配额超限
    MAINTENANCE_MODE = 45010  # 系统维护中

    # ============ 服务器错误 (50xxx) ============

    INTERNAL_SERVER_ERROR = 50000  # 服务器内部错误 (通用)
    SERVICE_UNAVAILABLE = 50001  # 服务不可用
    CONFIGURATION_ERROR = 50002  # 配置错误
    MEMORY_ERROR = 50003  # 内存错误
    DISK_SPACE_ERROR = 50004  # 磁盘空间不足
    NETWORK_ERROR = 50005  # 网络错误
    TIMEOUT_ERROR = 50006  # 超时错误

    # ============ 数据库错误 (51xxx) ============

    DATABASE_ERROR = 51000  # 数据库错误 (通用)
    DATABASE_CONNECTION_FAILED = 51001  # 数据库连接失败
    QUERY_FAILED = 51002  # 查询失败
    DATA_INTEGRITY_ERROR = 51003  # 数据完整性错误
    DUPLICATE_ENTRY = 51004  # 重复条目
    FOREIGN_KEY_CONSTRAINT = 51005  # 外键约束错误
    DATABASE_TIMEOUT = 51006  # 数据库超时
    TRANSACTION_ERROR = 51007  # 事务错误

    # ============ 外部服务错误 (52xxx) ============

    EXTERNAL_SERVICE_ERROR = 52000  # 外部服务错误 (通用)
    EXTERNAL_SERVICE_TIMEOUT = 52001  # 外部服务超时
    EXTERNAL_SERVICE_UNAVAILABLE = 52002  # 外部服务不可用
    API_LIMIT_EXCEEDED = 52003  # API调用次数超限
    EXTERNAL_API_ERROR = 52004  # 外部API错误
    PAYMENT_ERROR = 52005  # 支付错误
    NOTIFICATION_ERROR = 52006  # 通知发送失败
    EMAIL_SERVICE_ERROR = 52007  # 邮件服务错误

    # ============ AI/Agent 相关错误 (53xxx) ============

    AGENT_ERROR = 53000  # Agent错误 (通用)
    AGENT_NOT_FOUND = 53001  # Agent不存在
    AGENT_INITIALIZATION_FAILED = 53002  # Agent初始化失败
    AGENT_EXECUTION_FAILED = 53003  # Agent执行失败
    AGENT_TIMEOUT = 53004  # Agent执行超时
    AGENT_QUOTA_EXCEEDED = 53005  # Agent配额超限
    PROVIDER_ERROR = 53006  # Provider错误
    MODEL_NOT_AVAILABLE = 53007  # 模型不可用
    CONTEXT_TOO_LARGE = 53008  # 上下文过长

    @classmethod
    def get_http_status(cls, error_code: int) -> int:
        """
        根据错误码获取对应的HTTP状态码

        Args:
            error_code: 错误码

        Returns:
            int: HTTP状态码
        """
        # 根据错误码的类别确定HTTP状态码
        category = (error_code // 1000) % 100

        if category == 40:  # 通用错误
            return 400
        elif category == 41:  # 认证错误
            return 401
        elif category == 42:  # 验证错误
            return 422
        elif category == 43:  # 权限错误
            return 403
        elif category == 44:  # 资源错误
            return 404
        elif category == 45:  # 业务逻辑错误
            return 409
        elif category in [50, 51, 52, 53]:  # 服务器错误
            return 500
        else:
            # 默认返回500
            return 500

    @classmethod
    def is_client_error(cls, error_code: int) -> bool:
        """
        判断是否为客户端错误

        Args:
            error_code: 错误码

        Returns:
            bool: 是否为客户端错误
        """
        return 40000 <= error_code < 50000

    @classmethod
    def is_server_error(cls, error_code: int) -> bool:
        """
        判断是否为服务器错误

        Args:
            error_code: 错误码

        Returns:
            bool: 是否为服务器错误
        """
        return 50000 <= error_code < 60000

    @classmethod
    def get_category(cls, error_code: int) -> str:
        """
        获取错误码类别

        Args:
            error_code: 错误码

        Returns:
            str: 错误类别描述
        """
        category_map = {
            40: "通用错误",
            41: "认证错误",
            42: "验证错误",
            43: "权限错误",
            44: "资源错误",
            45: "业务逻辑错误",
            50: "服务器错误",
            51: "数据库错误",
            52: "外部服务错误",
            53: "AI/Agent错误"
        }

        category = (error_code // 1000) % 100
        return category_map.get(category, "未知错误")

    def description(self) -> str:
        """
        获取错误码的描述

        Returns:
            str: 错误码描述
        """
        descriptions = {
            # 通用错误
            ErrorCode.BAD_REQUEST: "请求参数错误",
            ErrorCode.INVALID_FORMAT: "请求格式错误",
            ErrorCode.INVALID_DATA: "请求数据无效",
            ErrorCode.MISSING_PARAMETER: "缺少必需参数",
            ErrorCode.INVALID_PARAMETER: "无效参数值",
            ErrorCode.UNSUPPORTED_MEDIA_TYPE: "不支持的媒体类型",
            ErrorCode.REQUEST_TOO_LARGE: "请求体过大",
            ErrorCode.RATE_LIMIT_EXCEEDED: "请求频率超限",

            # 认证错误
            ErrorCode.UNAUTHORIZED: "未认证",
            ErrorCode.INVALID_TOKEN: "token无效",
            ErrorCode.TOKEN_EXPIRED: "token过期",
            ErrorCode.AUTH_FAILED: "认证失败",
            ErrorCode.INVALID_CREDENTIALS: "凭据无效",
            ErrorCode.ACCOUNT_LOCKED: "账户被锁定",
            ErrorCode.ACCOUNT_SUSPENDED: "账户被暂停",
            ErrorCode.TOKEN_REVOKED: "token已被撤销",

            # 验证错误
            ErrorCode.VALIDATION_ERROR: "验证失败",
            ErrorCode.INVALID_FORMAT_FIELD: "字段格式错误",
            ErrorCode.INVALID_LENGTH: "字段长度错误",
            ErrorCode.INVALID_RANGE: "字段值超出范围",
            ErrorCode.REQUIRED_FIELD_MISSING: "必填字段缺失",
            ErrorCode.INVALID_EMAIL: "邮箱格式无效",
            ErrorCode.INVALID_PHONE: "电话格式无效",
            ErrorCode.INVALID_URL: "URL格式无效",
            ErrorCode.INVALID_DATE: "日期格式无效",
            ErrorCode.WEAK_PASSWORD: "密码强度不够",

            # 权限错误
            ErrorCode.FORBIDDEN: "权限不足",
            ErrorCode.ACCESS_DENIED: "访问被拒绝",
            ErrorCode.ACCOUNT_DISABLED: "账号被禁用",
            ErrorCode.INSUFFICIENT_PERMISSIONS: "权限不足，缺少所需权限",
            ErrorCode.ROLE_REQUIRED: "需要特定角色",
            ErrorCode.PREMIUM_REQUIRED: "需要高级权限",
            ErrorCode.ADMIN_REQUIRED: "需要管理员权限",

            # 资源错误
            ErrorCode.RESOURCE_NOT_FOUND: "资源不存在",
            ErrorCode.USER_NOT_FOUND: "用户不存在",
            ErrorCode.ROLE_NOT_FOUND: "角色不存在",
            ErrorCode.APPLICATION_NOT_FOUND: "应用不存在",
            ErrorCode.INVITE_CODE_NOT_FOUND: "邀请码不存在",
            ErrorCode.SESSION_NOT_FOUND: "会话不存在",
            ErrorCode.FILE_NOT_FOUND: "文件不存在",
            ErrorCode.CONFIG_NOT_FOUND: "配置不存在",
            ErrorCode.TASK_NOT_FOUND: "任务不存在",

            # 业务逻辑错误
            ErrorCode.USERNAME_ALREADY_EXISTS: "用户名已存在",
            ErrorCode.EMAIL_ALREADY_EXISTS: "邮箱已存在",
            ErrorCode.RESOURCE_ALREADY_EXISTS: "资源已存在",
            ErrorCode.INVITE_CODE_EXPIRED: "邀请码已过期",
            ErrorCode.INVITE_CODE_USED_UP: "邀请码已用完",
            ErrorCode.INVALID_OPERATION: "无效操作",
            ErrorCode.RESOURCE_CONFLICT: "资源冲突",
            ErrorCode.DEPENDENCY_ERROR: "依赖错误",
            ErrorCode.QUOTA_EXCEEDED: "配额超限",
            ErrorCode.MAINTENANCE_MODE: "系统维护中",

            # 服务器错误
            ErrorCode.INTERNAL_SERVER_ERROR: "服务器内部错误",
            ErrorCode.SERVICE_UNAVAILABLE: "服务不可用",
            ErrorCode.CONFIGURATION_ERROR: "配置错误",
            ErrorCode.MEMORY_ERROR: "内存错误",
            ErrorCode.DISK_SPACE_ERROR: "磁盘空间不足",
            ErrorCode.NETWORK_ERROR: "网络错误",
            ErrorCode.TIMEOUT_ERROR: "超时错误",

            # 数据库错误
            ErrorCode.DATABASE_ERROR: "数据库错误",
            ErrorCode.DATABASE_CONNECTION_FAILED: "数据库连接失败",
            ErrorCode.QUERY_FAILED: "查询失败",
            ErrorCode.DATA_INTEGRITY_ERROR: "数据完整性错误",
            ErrorCode.DUPLICATE_ENTRY: "重复条目",
            ErrorCode.FOREIGN_KEY_CONSTRAINT: "外键约束错误",
            ErrorCode.DATABASE_TIMEOUT: "数据库超时",
            ErrorCode.TRANSACTION_ERROR: "事务错误",

            # 外部服务错误
            ErrorCode.EXTERNAL_SERVICE_ERROR: "外部服务错误",
            ErrorCode.EXTERNAL_SERVICE_TIMEOUT: "外部服务超时",
            ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: "外部服务不可用",
            ErrorCode.API_LIMIT_EXCEEDED: "API调用次数超限",
            ErrorCode.EXTERNAL_API_ERROR: "外部API错误",
            ErrorCode.PAYMENT_ERROR: "支付错误",
            ErrorCode.NOTIFICATION_ERROR: "通知发送失败",
            ErrorCode.EMAIL_SERVICE_ERROR: "邮件服务错误",

            # AI/Agent错误
            ErrorCode.AGENT_ERROR: "Agent错误",
            ErrorCode.AGENT_NOT_FOUND: "Agent不存在",
            ErrorCode.AGENT_INITIALIZATION_FAILED: "Agent初始化失败",
            ErrorCode.AGENT_EXECUTION_FAILED: "Agent执行失败",
            ErrorCode.AGENT_TIMEOUT: "Agent执行超时",
            ErrorCode.AGENT_QUOTA_EXCEEDED: "Agent配额超限",
            ErrorCode.PROVIDER_ERROR: "Provider错误",
            ErrorCode.MODEL_NOT_AVAILABLE: "模型不可用",
            ErrorCode.CONTEXT_TOO_LARGE: "上下文过长",
        }

        return descriptions.get(self, "未知错误")


# 错误码分类常量
class ErrorCategory:
    """错误码分类常量"""

    CLIENT_ERROR = "CLIENT_ERROR"  # 客户端错误
    SERVER_ERROR = "SERVER_ERROR"  # 服务器错误

    # 具体分类
    GENERAL = "GENERAL"  # 通用错误
    AUTH = "AUTH"  # 认证错误
    VALIDATION = "VALIDATION"  # 验证错误
    PERMISSION = "PERMISSION"  # 权限错误
    RESOURCE = "RESOURCE"  # 资源错误
    BUSINESS = "BUSINESS"  # 业务逻辑错误
    DATABASE = "DATABASE"  # 数据库错误
    EXTERNAL = "EXTERNAL"  # 外部服务错误
    AI_AGENT = "AI_AGENT"  # AI/Agent错误


# 常用错误码快捷访问
class CommonErrors:
    """常用错误码快捷访问"""

    # 最常用的错误码
    BAD_REQUEST = ErrorCode.BAD_REQUEST
    UNAUTHORIZED = ErrorCode.UNAUTHORIZED
    FORBIDDEN = ErrorCode.FORBIDDEN
    NOT_FOUND = ErrorCode.RESOURCE_NOT_FOUND
    VALIDATION_ERROR = ErrorCode.VALIDATION_ERROR
    INTERNAL_ERROR = ErrorCode.INTERNAL_SERVER_ERROR

    # 用户相关
    USER_NOT_FOUND = ErrorCode.USER_NOT_FOUND
    USERNAME_EXISTS = ErrorCode.USERNAME_ALREADY_EXISTS
    EMAIL_EXISTS = ErrorCode.EMAIL_ALREADY_EXISTS
    WEAK_PASSWORD = ErrorCode.WEAK_PASSWORD

    # 资源相关
    RESOURCE_EXISTS = ErrorCode.RESOURCE_ALREADY_EXISTS
    RESOURCE_CONFLICT = ErrorCode.RESOURCE_CONFLICT

    # 系统相关
    SERVICE_UNAVAILABLE = ErrorCode.SERVICE_UNAVAILABLE
    MAINTENANCE = ErrorCode.MAINTENANCE_MODE
    RATE_LIMIT = ErrorCode.RATE_LIMIT_EXCEEDED