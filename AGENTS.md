# 项目开发指南

- 使用中文进行对话
- 每次开启新对话时自动加载项目上下文：参考[上下文管理原则](#上下文管理原则)

---

## 1. 技术栈

- backend: Python
- frontend: Next.JS + Tailwind + Shadcn/ui + Lucide-react icons
- database: Postgres

---

## 2. 项目目录结构

核心目录与文件：
- `ai_memory/`: AI编码助手（`Codex`/`Claude Code`/`Gemini`）公用的临时记忆
    + project：项目级上下文
    + features：Feature开发临时文件，比如：需求文档、设计文档、开发计划等，帮助AI Coding Agent理解开发任务
    + docs：第三方库集成参考文档，提供给AI Coding Agent参考
    + references：第三方库代码，提供给AI Coding Agent参考
- `backend/`: 后端代码根目录
  - 数据库访问架构：严格遵循Router → Service → Repository → Database分层模式，100%通过服务层访问数据库
- `frontend/copilotkit-web-ui`：前端代码根目录
- `docs/`: 项目级文档
- `justfile`: Just命令
- `pyproject.toml`：Python项目管理文件

---

## 3. 包管理工具

- Python: `uv` command. 进入`backend/`目录，执行`source .venv/bin/activate`来激活uv虚拟环境
- Javascript: `npm` command

---

## 4. 核心决策原则

在做任何决策前应当遵从如下原则：
- First Principles Thinking：将复杂问题分解到基本事实
- KISS (Keep It Simple, Stupid): 优先选择简单、直接、可行的解决方案，而非过度复杂或抽象的方案。
- DRY (Don't Repeat Yourself): 通过函数、类和模块最大化代码复用。避免复制粘贴逻辑。
- YAGNI (You Ain't Gonna Need It): 不要实现未被明确要求或当前任务非必需的功能。

---

## 5. 用户偏好

### User Interaction Preferences

1. Always response in Simplified Chinese

2. 只在以下情况汇报/总结工作：
    - 用户明确要求总结（如"总结一下你做了什么"）
    - 需要向用户报告进度或遇到的问题
    - 多阶段任务的中间检查点

3. **NEVER CREATE REPORT DOCUMENT WHEN A TASK IS FINISHED**：直接完成任务，不主动输出总结报告
    - 除非任务失败需要说明原因
    - 除非有重要的警告或注意事项
    - 用户可以看到文件系统的变化，无需重复说明

4. 当用户给出"简单总结"等限定词时，严格遵守

核心原则：
- ❌ 不要"猜测"什么时候应该汇报
- ✅ 只在明确被要求时才汇报
- ✅ 完成即完成，信息在文件系统中已有体现

### Shell Command Preferences (fast defaults + portable fallbacks)

> IMPORTANT: If prefered tool is not available, then fallback to default tool. Prefer one cli command over multiple tool calls.

1. Text search: prefer `rg` (ripgrep) over `grep`
    - Structured output when needed: `rg --json '...' | jq -c '.'` (if `jq` is available).
2. File finding: prefer `fdfind` over `find`
3. Preview: prefer `bat` over `cat`
4. Bulk text replace — prefer `sd` over `sed`

**Safety notes**
- For pipelines of filenames, always prefer **null-delimited** (`-print0`, `-0`, `xargs -0`).
- For large repos, **exclude** dirs early (`-g`/`-E`) instead of post-filtering.
- Prefer **dry-run** flags when available.

### Bug Fix Preferences

- **NEVER BYPASS AN ISSUE**：修复问题时，应当深入分析产生问题的**根本原因**，不要试图使用**Workaround**绕过问题。

### Documentation Preferences

文档包括各种markdown文档和代码中的注释文档。创建文档时，遵循以下原则：
1. 只按照用户的要求来创建文档，不得随意创建文档。
2. 代码是最好的文档，优先使用代码注释来解释代码逻辑。当代码逻辑发生变化时，代码注释必须同步更新。
3. 文档数量越少越好，一份文档好于多份文档。

### Debug Preferences

1. 访问`http://localhost:8000/docs#/`获取后端OpenAPI接口列表详细信息
2. 使用`chrome-devtools`工具来访问前端页面
3. **NEVER**尝试启动前后端服务，如果需要启动/重启服务，**MUST**请求用户来执行。你的职责**不包含启动前后端服务**！

### 参考文档路径

项目会引用第三方库，为了方便查询，会在项目中缓存第三方文档或者代码，存放路径如下：
1. 参考文档：`ai_memory/docs/`
2. 第三方代码库：`ai_memory/references/`，每个子目录是一个第三方项目库
3. 在线文档：使用`context7`/`search`/`fetch`来实时查询