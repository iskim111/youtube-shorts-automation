# Portable FFmpeg → tools/ffmpeg/ (프로젝트 로컬, 관리자 권한 불필요)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$ToolsDir = Join-Path $Root "tools\ffmpeg"
New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null

$Version = "7.1.1"
$ZipUrl = "https://github.com/GyanD/codexffmpeg/releases/download/$Version/ffmpeg-$Version-essentials_build.zip"
$ZipPath = Join-Path $env:TEMP "ffmpeg-$Version.zip"
$ExtractDir = Join-Path $env:TEMP "ffmpeg-$Version-extract"

Write-Host "[ffmpeg] downloading $Version ..."
Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
if (Test-Path $ExtractDir) { Remove-Item $ExtractDir -Recurse -Force }
Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

$Inner = Get-ChildItem $ExtractDir -Directory | Select-Object -First 1
Copy-Item (Join-Path $Inner.FullName "bin\ffmpeg.exe") $ToolsDir -Force
Copy-Item (Join-Path $Inner.FullName "bin\ffprobe.exe") $ToolsDir -Force

$env:FFMPEG_PATH = Join-Path $ToolsDir "ffmpeg.exe"
& $env:FFMPEG_PATH -version | Select-Object -First 1
Write-Host "[ffmpeg] installed to $ToolsDir"
Write-Host "Set in .env: FFMPEG_PATH=$($env:FFMPEG_PATH)"
