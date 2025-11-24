# smartrade-adk
A smart trade agent.

## 项目概述

本项目基于[Google ADK](https://github.com/google/adk-python)和[AG-UI](https://github.com/ag-ui-protocol/ag-ui)构建的A股投资智能体。

## 技术栈

- 后端：Python 3.8 + FastAPI + Google ADK + AG-UI
- 前端：Next.js + Shadcn/ui + Tailwind CSS + Lucide-react

## 如何使用

1. 克隆项目到本地

```bash
git clone https://github.com/your-username/smartrade-adk.git
```

2. 安装依赖

```bash
cd smartrade-adk
pip install -r requirements.txt
```

3. 启动后端

```bash
just run-backend-in-memory
```

4. 启动前端

```bash
just run-frontend
```

5. 访问前端页面

在浏览器中访问`http://localhost:3000`即可看到前端页面。
