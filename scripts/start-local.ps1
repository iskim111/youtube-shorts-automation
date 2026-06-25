# 로컬 파일럿 실행 (SQLite, Docker 불필요)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..").Path

$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$EnvFile = Join-Path $Root ".env"

$FfmpegExe = Join-Path $Root "tools\ffmpeg\ffmpeg.exe"
if (-not (Test-Path $FfmpegExe)) {
    Write-Host "[ffmpeg] not found — running install-ffmpeg.ps1"
    & (Join-Path $Root "scripts\install-ffmpeg.ps1")
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $Root ".env.example") $EnvFile
    (Get-Content $EnvFile -Raw) -replace 'postgresql\+asyncpg://.*', 'sqlite+aiosqlite:///./data/shorts.db' |
        Set-Content $EnvFile -Encoding UTF8
    Write-Host "[env] .env created (SQLite mode)"
}

$FfmpegPath = Join-Path $Root "tools\ffmpeg\ffmpeg.exe"
Write-Host "[backend] starting uvicorn on :8000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Backend'; `$env:PYTHONPATH='$Backend'; `$env:FFMPEG_PATH='$FfmpegPath'; uvicorn app.main:app --reload --port 8000"
) | Out-Null

Start-Sleep -Seconds 3

$FrontendPort = 3001
Write-Host "[frontend] starting next dev on :$FrontendPort ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Frontend'; `$env:PORT='$FrontendPort'; npm run dev"
) | Out-Null

Write-Host ""
Write-Host "Dashboard: http://localhost:$FrontendPort"
Write-Host "API docs:  http://localhost:8000/docs"
Write-Host "Pilot:     python backend/scripts/run_pilot.py"
