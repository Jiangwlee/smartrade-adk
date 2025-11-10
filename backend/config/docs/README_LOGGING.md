# 全局日志系统使用指南

## 概述

项目使用统一的日志配置模块 `backend/config/logging.py`，提供：

- ✅ **双重输出**：终端彩色输出 + 文件持久化
- ✅ **日志轮转**：按日期自动轮转，保留历史记录
- ✅ **多种格式**：支持 JSON 和 TEXT 两种格式
- ✅ **分级存储**：错误日志单独存储，保留更久
- ✅ **自动配置**：应用启动时自动初始化

## 快速开始

### 1. 在模块中使用日志

```python
from backend.config.logging import get_logger

logger = get_logger(__name__)

# 使用日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 2. 配置日志级别和格式

在 `.env` 文件中配置：

```bash
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 日志格式：json 或 text
LOG_FORMAT=text
```

## 日志输出位置

### 终端输出
- 彩色格式，便于开发调试
- 级别：根据 `LOG_LEVEL` 配置

### 文件输出

日志文件存储在项目根目录的 `log/` 目录下：

```
log/
├── app.log          # 所有级别的日志
├── app.log.2025-01-08  # 按日期轮转的历史日志
├── error.log        # 仅 ERROR 及以上级别
└── error.log.2025-01-08
```

#### 轮转策略

| 文件 | 轮转时间 | 保留天数 |
|------|----------|----------|
| `app.log` | 每天午夜 | 30 天 |
| `error.log` | 每天午夜 | 90 天 |

## 日志格式

### TEXT 格式（默认）

**终端输出（带颜色）：**
```
2025-01-08 10:30:45 - INFO - backend.api.endpoint - 🚀 Running agent: adk_demo
```

**文件输出（详细）：**
```
2025-01-08 10:30:45 - INFO - backend.api.endpoint - [endpoint.py:124] - 🚀 Running agent: adk_demo
```

### JSON 格式

```json
{
  "timestamp": "2025-01-08T02:30:45.123456",
  "level": "INFO",
  "logger": "backend.api.endpoint",
  "message": "🚀 Running agent: adk_demo",
  "module": "endpoint",
  "function": "run",
  "line": 124
}
```

## 高级用法

### 手动初始化日志系统

```python
from backend.config.logging import setup_logging

# 自定义配置
setup_logging(
    log_level="DEBUG",           # 覆盖配置文件
    log_format="json",           # JSON 格式
    enable_console=True,         # 启用终端输出
    enable_file=True,            # 启用文件输出
)
```

### 添加额外字段（JSON 格式）

```python
import logging
from backend.config.logging import get_logger

logger = get_logger(__name__)

# 记录带额外字段的日志
extra = {"user_id": "123", "request_id": "abc"}
logger.info("用户操作", extra={"extra_fields": extra})
```

## 第三方库日志控制

系统已自动配置常用第三方库的日志级别：

- `uvicorn`: INFO
- `uvicorn.access`: WARNING（减少访问日志）
- `fastapi`: INFO
- `sqlalchemy`: WARNING
- `watchdog`: WARNING

## 最佳实践

### ✅ 推荐

```python
# 1. 使用模块级 logger
from backend.config.logging import get_logger
logger = get_logger(__name__)

# 2. 使用合适的日志级别
logger.debug("详细的调试信息")      # 开发环境
logger.info("重要的业务信息")       # 正常流程
logger.warning("可恢复的异常")      # 需要注意
logger.error("错误信息", exc_info=True)  # 包含堆栈
logger.critical("严重错误")         # 需要立即处理

# 3. 记录有价值的信息
logger.info(f"用户 {user_id} 执行操作: {action}")

# 4. 异常时包含堆栈信息
try:
    risky_operation()
except Exception as e:
    logger.error(f"操作失败: {e}", exc_info=True)
```

### ❌ 避免

```python
# 1. 不要使用 print()
print("这条信息不会被记录到文件")  # ❌

# 2. 不要记录敏感信息
logger.info(f"密码: {password}")  # ❌

# 3. 不要在循环中打印大量日志
for item in large_list:
    logger.info(item)  # ❌ 可能淹没日志

# 4. 不要使用字符串拼接
logger.info("User: " + str(user_id))  # ❌
logger.info(f"User: {user_id}")       # ✅
```

## 故障排查

### 问题：日志不输出到终端

**可能原因**：
- 日志级别设置过高（如 ERROR），INFO 日志不会显示

**解决方案**：
```bash
# .env 文件
LOG_LEVEL=INFO
```

### 问题：日志文件没有生成

**可能原因**：
- `log/` 目录权限问题
- 日志系统未初始化

**解决方案**：
```bash
# 检查目录权限
ls -la log/

# 确保应用启动时调用了 setup_logging()
```

### 问题：日志格式不正确

**可能原因**：
- 多个模块重复初始化日志系统

**解决方案**：
- 确保 `setup_logging()` 只在应用启动时调用一次
- 在其他模块中只使用 `get_logger(__name__)`

## 配置参考

### settings.py 配置项

```python
# 日志配置
log_level: str = "INFO"          # 日志级别
log_format: str = "json"         # 日志格式 (json/text)
```

### 环境变量

```bash
# .env 文件
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

## 参考资料

- [Python logging 官方文档](https://docs.python.org/3/library/logging.html)
- [日志最佳实践](https://docs.python.org/3/howto/logging.html#logging-basic-tutorial)
