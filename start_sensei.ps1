# Sensei - one-click launcher (ASCII-only, PowerShell 5.1 compatible)
# --------------------------------------------------------------------
# Usage:   .\start_sensei.ps1              (double-click friendly via
#          right-click > Run with PowerShell)
#
# What it does, in order:
#   1. Make sure the Ollama daemon is reachable (starts it if not)
#   2. Make sure the Gemma 4 model is pulled
#   3. Make sure the Python deps import
#   4. Start python -m frontend.app in this window
#   5. Wait until http://localhost:7860/display answers, then open the
#      operator console and the projector view in the default browser
#
# Close this window (or Ctrl+C) to stop Sensei.
#
# Keep this file ASCII-only: PowerShell 5.1 parses .ps1 files with the
# system code page and mangles Chinese characters (see dry_run.ps1).

param(
    [string]$Model = "gemma4:e2b",
    [int]$Port = 7860,
    [switch]$NoBrowser
)

Set-Location -Path $PSScriptRoot
# Same pairing as dry_run.ps1: PYTHONIOENCODING makes the app emit UTF-8, and
# the Console line sets the console output code page so its Chinese startup
# banner renders instead of coming out as CP950 mojibake.
$env:PYTHONIOENCODING = "utf-8"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

function Say([string]$msg)  { Write-Host "  $msg" }
function Ok([string]$msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Die([string]$msg)  { Write-Host "  [FAIL] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host " Sensei - on-device AI co-teacher " -ForegroundColor White -BackgroundColor DarkBlue
Write-Host ""

# 1. Ollama daemon ---------------------------------------------------
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Die "ollama not found on PATH. Install from https://ollama.com and re-run."
}
$ollamaUrl = "http://localhost:11434/api/tags"
function OllamaUp {
    try { Invoke-RestMethod -Uri $ollamaUrl -TimeoutSec 2 | Out-Null; return $true }
    catch { return $false }
}
if (OllamaUp) {
    Ok "Ollama daemon is running"
} else {
    Say "Ollama daemon not reachable; starting 'ollama serve' in the background..."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden | Out-Null
    $tries = 0
    while (-not (OllamaUp) -and $tries -lt 20) { Start-Sleep -Seconds 1; $tries++ }
    if (OllamaUp) { Ok "Ollama daemon started" } else { Die "Ollama did not come up within 20 s. Start it manually (ollama serve) and re-run." }
}

# 2. Model -----------------------------------------------------------
$tags = Invoke-RestMethod -Uri $ollamaUrl -TimeoutSec 5
$have = @()
if ($tags.models) { $have = $tags.models | ForEach-Object { $_.name } }
if ($have -contains $Model) {
    Ok "Model $Model is available"
} else {
    Warn "Model $Model is not pulled yet (have: $($have -join ', '))"
    Say  "Pulling now; this is a one-time ~7 GB download..."
    & ollama pull $Model
    if ($LASTEXITCODE -ne 0) { Die "ollama pull $Model failed" }
    Ok "Model $Model pulled"
}

# 3. Python deps -----------------------------------------------------
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Die "python not found on PATH" }
& python -c "import gradio, faster_whisper, ollama, pydantic, sounddevice, soundfile" 2>$null
if ($LASTEXITCODE -ne 0) {
    Die "Python deps missing. Run: pip install -r requirements.txt  (and PyTorch, see README)"
}
Ok "Python deps import"

# 4. Start the app ----------------------------------------------------
$displayUrl = "http://localhost:$Port/display"
try { Invoke-WebRequest -Uri $displayUrl -TimeoutSec 2 -UseBasicParsing | Out-Null; $already = $true } catch { $already = $false }
if ($already) {
    Warn "Something already answers on port $Port; not starting a second Sensei."
} else {
    Say "Starting Sensei (models load in ~60 s on first run)..."
    $proc = Start-Process -FilePath "python" -ArgumentList "-m", "frontend.app" -NoNewWindow -PassThru
    $tries = 0
    $up = $false
    while (-not $up -and $tries -lt 180) {
        Start-Sleep -Seconds 1
        $tries++
        if ($proc.HasExited) { Die "Sensei exited early (exit code $($proc.ExitCode)). Scroll up for the error." }
        try { Invoke-WebRequest -Uri $displayUrl -TimeoutSec 2 -UseBasicParsing | Out-Null; $up = $true } catch { }
    }
    if (-not $up) { Die "Sensei did not answer on port $Port within 3 minutes." }
    Ok "Sensei is serving on http://localhost:$Port"
}

# 5. Browser tabs -----------------------------------------------------
if (-not $NoBrowser) {
    Start-Process "http://localhost:$Port/"
    Start-Sleep -Milliseconds 800
    Start-Process $displayUrl
    Say "Opened the operator console and /display."
    Say "Drag the /display tab to the projector screen and press F11."
}

Write-Host ""
Write-Host " Sensei is running. Close this window or press Ctrl+C to stop. " -ForegroundColor White -BackgroundColor DarkGreen
Write-Host ""
if ($proc) { Wait-Process -Id $proc.Id }
