set dotenv-load := true
set export

# Backend commands - 统一的 web server 管理
run-backend servers="all":
    @echo "🚀 启动后端服务: {{servers}}"
    ./backend/.venv/bin/python -m backend.cli.run_web_server start --servers={{servers}}

stop-backend servers="all":
    @echo "🛑 停止后端服务: {{servers}}"
    ./backend/.venv/bin/python -m backend.cli.run_web_server stop --servers={{servers}}

run-adk:
    @echo "🚀 启动ADK服务"
    adk web backend/agents --session_service_uri=$SUPABASE_DATABASE_URL