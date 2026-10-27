$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectPath
$pythonPath = Join-Path $projectPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create Python 3.12 .venv first' }
docker compose up -d --wait db
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL startup failed' }
& $pythonPath -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migration failed' }
& $pythonPath -m uvicorn src.main:app --host 127.0.0.1 --port 8001 --reload --no-access-log
