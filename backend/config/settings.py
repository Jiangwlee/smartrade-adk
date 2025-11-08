"""
统一配置管理（使用 Pydantic Settings）

从环境变量或 .env 文件读取配置
"""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    app_name: str = "SWKJ Agents Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"  # development / staging / production

    # 数据库配置
    database_url: str = "postgresql://swkj:swkj_password@localhost:5432/swkj_agents"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False  # SQL 日志

    # 测试数据库（可选）
    test_database_url: Optional[str] = None

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 7 * 24 * 3600  # 7 天（秒）
    redis_cache_ttl: int = 3600  # 1 小时（秒）

    # JWT 认证配置
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24  # 24 小时

    # JWT 密钥管理配置
    jwt_key_rotation_days: int = 90  # 密钥轮换间隔（天）
    jwt_key_grace_period_days: int = 7  # 密钥优雅期（天）
    jwt_keys_file_path: Optional[str] = None  # 密钥文件路径，None表示使用默认路径
    jwt_auto_rotation: bool = True  # 是否自动轮换密钥

    # CORS 配置
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # Provider 配置
    doubao_api_key: Optional[str] = None
    google_cloud_project: Optional[str] = None
    google_cloud_location: Optional[str] = None

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json / text

    # 用户管理配置
    max_username_length: int = 50
    max_email_length: int = 255
    max_password_length: int = 128
    min_password_length: int = 6

    # 分页配置
    default_page_size: int = 20
    max_page_size: int = 100
    default_search_limit: int = 20

    # 邀请码配置
    default_invite_max_use: int = 1
    default_invite_expires_days: int = 30
    max_batch_invite_count: int = 100

    # 角色配置
    default_role_name: str = "User"
    system_role_names: List[str] = ["Administrator", "User"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 忽略额外的环境变量
    )

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS origins，支持字符串和列表格式"""
        if isinstance(v, str):
            # 如果是字符串，尝试按逗号分割
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator('cors_methods', mode='before')
    @classmethod
    def parse_cors_methods(cls, v):
        """解析 CORS methods，支持字符串和列表格式"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @field_validator('cors_headers', mode='before')
    @classmethod
    def parse_cors_headers(cls, v):
        """解析 CORS headers，支持字符串和列表格式"""
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v):
        """验证日志格式"""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid log format: {v}. Must be one of {valid_formats}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment.lower() == "development"

    @property
    def is_staging(self) -> bool:
        """是否为预发布环境"""
        return self.environment.lower() == "staging"


# 全局单例
settings = Settings()