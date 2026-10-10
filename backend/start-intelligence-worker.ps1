$ErrorActionPreference = 'Stop'
$intelligenceRoot = $PSScriptRoot
$intelligencePython = Join-Path $intelligenceRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $intelligencePython)) { throw 'Create the backend virtual environment and install requirements.txt first.' }
Push-Location -LiteralPath $intelligenceRoot
try {
    & $intelligencePython -c "import asyncio,sys; from app.workers.queue import health; sys.exit(0 if asyncio.run(health())['jobQueue']=='healthy' else 1)"
    if ($LASTEXITCODE -ne 0) { throw 'Redis is unavailable. Configure REDIS_URL or start the Redis Compose service first.' }
    $intelligenceExisting = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*-m app.workers.tasks*' -and $_.Name -like '*python*' }
    if ($intelligenceExisting) { Write-Output 'An intelligence worker is already running.'; return }
    $intelligenceLogs = Join-Path $intelligenceRoot 'tmp'
    New-Item -ItemType Directory -Path $intelligenceLogs -Force | Out-Null
    Start-Process -FilePath $intelligencePython -ArgumentList '-m app.workers.tasks' -WorkingDirectory $intelligenceRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $intelligenceLogs 'intelligence-worker.log') -RedirectStandardError (Join-Path $intelligenceLogs 'intelligence-worker-error.log')
    Write-Output 'Worker started. Check /health/intelligence for its heartbeat.'
} finally { Pop-Location }
