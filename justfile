set dotenv-load := true
set export

# Backend commands - 统一的 web server 管理
run-backend servers="all":
    @echo "🚀 启动后端服务: {{servers}}"
    ./backend/.venv/bin/python -m backend.cli.run_web_server start --session-service-uri=$SUPABASE_DATABASE_URL --servers={{servers}}

run-backend-in-memory:
    @echo "🚀 启动后端服务：使用InMemory数据库"
    ./backend/.venv/bin/python -m backend.cli.run_web_server start --servers=smartrade

stop-backend servers="all":
    @echo "🛑 停止后端服务: {{servers}}"
    ./backend/.venv/bin/python -m backend.cli.run_web_server stop --servers={{servers}}

run-adk:
    @echo "🚀 启动ADK服务"
    adk web backend/agents --session_service_uri=$SUPABASE_DATABASE_URL

run-frontend:
    @echo "🚀 启动Smartrade前端服务"
    cd frontend/copilotkit-with-supabase && npm run dev

