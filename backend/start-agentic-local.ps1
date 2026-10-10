param([switch]$SkipLocalRedis)
$ErrorActionPreference = 'Stop'
$agenticRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $agenticRoot
$agenticPython = Join-Path $agenticRoot '.venv\Scripts\python.exe'
$agenticLogs = Join-Path $agenticRoot 'tmp'
New-Item -ItemType Directory -Path $agenticLogs -Force | Out-Null
function Test-AgenticPort([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}
if (-not (Test-Path -LiteralPath $agenticPython)) { throw 'Backend virtual environment is missing.' }
if (-not $SkipLocalRedis -and -not (Test-AgenticPort 6379)) {
    # Existing user-local official Ubuntu Redis package; no installation/sudo.
    & wsl.exe -d Ubuntu -- sh -lc 'LD_LIBRARY_PATH=/home/chandu/.local/share/nexvora-redis/root/usr/lib/x86_64-linux-gnu /home/chandu/.local/share/nexvora-redis/root/usr/bin/redis-server --bind 127.0.0.1 --port 6379 --protected-mode yes --daemonize yes --appendonly yes --maxmemory 256mb --maxmemory-policy noeviction --dir /home/chandu/.local/share/nexvora-redis/data --pidfile /home/chandu/.local/share/nexvora-redis/redis.pid --logfile /home/chandu/.local/share/nexvora-redis/redis.log'
    if ($LASTEXITCODE -ne 0) { throw 'Local Redis could not start. For an external Redis service use -SkipLocalRedis.' }
}
if (-not (Test-AgenticPort 8003)) {
    Start-Process -FilePath (Join-Path $agenticRoot '.venv\Scripts\chroma.exe') -ArgumentList 'run --path data/chroma --host 127.0.0.1 --port 8003' -WorkingDirectory $agenticRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $agenticLogs 'chroma-live.log') -RedirectStandardError (Join-Path $agenticLogs 'chroma-live-error.log')
}
if (-not (Test-AgenticPort 8001)) {
    Start-Process -FilePath $agenticPython -ArgumentList '-m uvicorn app.main:app --host 127.0.0.1 --port 8001' -WorkingDirectory $agenticRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $agenticLogs 'api-live.log') -RedirectStandardError (Join-Path $agenticLogs 'api-live-error.log')
}
$existingWorker = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($agenticPython) -and $_.CommandLine -like '*-m app.workers.tasks*' }
if (-not $existingWorker) {
    Start-Process -FilePath $agenticPython -ArgumentList '-m app.workers.tasks' -WorkingDirectory $agenticRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $agenticLogs 'worker-live.log') -RedirectStandardError (Join-Path $agenticLogs 'worker-live-error.log')
}
if (-not (Test-AgenticPort 3000)) {
    $agenticNode = (Get-Command node.exe).Source
    $vitePath = Join-Path $projectRoot 'node_modules\vite\bin\vite.js'
    Start-Process -FilePath $agenticNode -ArgumentList ('"{0}" --port 3000 --host 127.0.0.1' -f $vitePath) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $agenticLogs 'frontend-live.log') -RedirectStandardError (Join-Path $agenticLogs 'frontend-live-error.log')
}
Write-Output 'NexVora services started or existing ports retained. No existing process was stopped.'
Write-Output 'App: http://localhost:3000/agent-hub'
Write-Output 'Check actual readiness at http://127.0.0.1:8001/api/v1/health/agentic after startup; logs are in backend/tmp.'
