# Sensei - preflight check (ASCII-only)
# ----------------------------------------------
# Usage:   .\dry_run.ps1
#
# Chinese-aware smoke tests are delegated to dry_run_smoke.py so PowerShell
# 5.1's system-codepage parsing of .ps1 source never sees non-ASCII bytes.
#
# Re-runnable, nothing destructive. ~45-60 s total (Whisper loads in step 7).
# Steps 1-7 check the models and devices; step 8 checks the B1 gate and the
# B3 session / handout paths without loading anything.

Set-Location -Path $PSScriptRoot

$pass = 0
$fail = 0
$warn = 0
$failed_steps = @()

function Step([string]$title, [scriptblock]$block) {
    Write-Host ""
    Write-Host "-- $title --" -ForegroundColor Cyan
    try { & $block } catch { Fail "unexpected error: $_" }
}
function Ok([string]$msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green;  $script:pass++ }
function Fail([string]$msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red;    $script:fail++; $script:failed_steps += $msg }
function Warn([string]$msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow; $script:warn++ }
function Hint([string]$msg) { Write-Host "         $msg" -ForegroundColor DarkGray }

# Force UTF-8 for any child process stdout that prints Chinese (smoke helper).
$env:PYTHONIOENCODING = "utf-8"

Write-Host ""
Write-Host " Sensei preflight " -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "Working dir: $PSScriptRoot" -ForegroundColor DarkGray
Write-Host "Start time : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray

# 1. Env vars
Step "1. Environment variables" {
    if ($env:HF_HOME -eq "D:\hf-cache") {
        Ok "HF_HOME = D:\hf-cache"
    } else {
        Fail "HF_HOME = '$($env:HF_HOME)' (expected D:\hf-cache)"
        Hint "Fix: [Environment]::SetEnvironmentVariable('HF_HOME','D:\hf-cache','User')"
    }
    if ($env:HF_ENDPOINT -eq "https://hf-mirror.com") {
        Ok "HF_ENDPOINT = https://hf-mirror.com"
    } else {
        Warn "HF_ENDPOINT = '$($env:HF_ENDPOINT)' (expected https://hf-mirror.com; slower without it but not blocking)"
    }
}

# 2. Whisper cache
Step "2. Faster-Whisper large-v3 in HF cache" {
    $whisper_dir = "D:\hf-cache\hub\models--Systran--faster-whisper-large-v3"
    if (Test-Path $whisper_dir) {
        Ok "$whisper_dir exists"
    } else {
        Fail "Whisper cache not found at $whisper_dir"
        Hint "Pre-load: python -c `"from faster_whisper import WhisperModel; WhisperModel('large-v3')`""
    }
}

# 3. Ollama + gemma4:e2b
Step "3. Ollama daemon + gemma4:e2b model" {
    $list = ollama list 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Fail "ollama list failed"
        Hint "Start Ollama (taskbar icon, or run 'ollama serve')"
        return
    }
    Ok "Ollama daemon reachable"
    if ($list -match "gemma4:e2b") {
        Ok "gemma4:e2b is pulled"
    } else {
        Fail "gemma4:e2b not pulled"
        Hint "Run: ollama pull gemma4:e2b"
    }
}

# 4. Python deps
Step "4. Python dependencies importable" {
    $out = python -c "import ollama, faster_whisper, gradio, pydantic, sounddevice; print('OK')" 2>&1 | Out-String
    if ($out -match "OK") {
        Ok "ollama, faster_whisper, gradio, pydantic, sounddevice all importable"
    } else {
        Fail "one or more imports failed"
        Hint $out.Trim()
    }
}

# 5. Audio devices (eyeball the right mic)
Step "5. Audio input devices (confirm your external mic is listed)" {
    $out = python dry_run_smoke.py audio 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Ok "input devices enumerated:"
        Write-Host $out.TrimEnd() -ForegroundColor White
    } else {
        Fail "could not enumerate audio devices"
        Hint $out.Trim()
    }
}

# 6. LLM smoke (enumeration)
Step "6. LLM smoke: canonical PID prompt -> expect enumeration_cards" {
    $out = python dry_run_smoke.py enum 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $out -match "PASS") {
        Ok "model correctly picked enumeration_cards"
    } else {
        Fail "enumeration_cards smoke failed"
        Write-Host ($out -split "`n" | Select-Object -Last 12 | Out-String) -ForegroundColor DarkGray
    }
}

# 7. Pipeline smoke + quiz spoken-trigger
Step "7. Pipeline smoke: quiz wake-phrase -> expect quiz_card + trigger fired" {
    Hint "(loads Whisper too, ~20-30 s)"
    $out = python dry_run_smoke.py quiz 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $out -match "PASS") {
        Ok "spoken-trigger fired AND template=quiz_card"
    } elseif ($out -match "WARN ") {
        Warn "quiz_card produced but spoken-trigger guard not exercised"
        Hint "Model picked it on its own this time; demo-day the guard still applies in pipeline.py"
    } else {
        Fail "quiz pipeline smoke failed"
        Write-Host ($out -split "`n" | Select-Object -Last 20 | Out-String) -ForegroundColor DarkGray
    }
}

# 8. B1 gate + B3 session / handout (no model loads, fast)
Step "8. Continuous-listening gate + lecture session + handout export" {
    $out = python dry_run_smoke.py gate 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $out -match "PASS") {
        Ok "gate thresholds, no_card tool, session dir and handout export"
        Write-Host ($out -split "`n" | Where-Object { $_ -match "content=" } | Out-String) -ForegroundColor DarkGray
    } else {
        Fail "gate / session / handout smoke failed"
        Write-Host ($out -split "`n" | Select-Object -Last 12 | Out-String) -ForegroundColor DarkGray
    }
    Hint "Tune the segmenter separately: python -m bench.segmenter_probe"
}

# 9. Manual checklist (no-script, just prints)
Step "9. Manual pre-lecture checks (script can't verify these for you)" {
    $items = @(
        "Launch app:    .\start_sensei.ps1   (or python -m frontend.app)",
        "Open /display: http://localhost:7860/display  ->  F11 fullscreen",
        "Type the course name and press 'start lecture' BEFORE the first card",
        "Pick theme:    Paper for warm light, Dark for dim room, Light for bright room",
        "Windows Sound -> input device matches the external mic in step 5",
        "Laptop battery 100%, power plugged, sleep + notifications disabled",
        "Speak the quiz wake-phrase INTO YOUR ACTUAL MICROPHONE and confirm Whisper transcribes it cleanly",
        "Start continuous listening, talk for two minutes, and watch the skip log:",
        "   too many cards -> raise GATE_MIN_CONTENT in core/pipeline.py",
        "   too few cards  -> lower it, or shorten MIN_UTTERANCE_S in core/live_mic.py",
        "   cards arrive late -> the queue is dropping; check the 'dropped' counter",
        "After the lecture: press 'export handout' and open the file it hands back"
    )
    foreach ($i in $items) { Hint "[ ] $i" }
}

# Summary
Write-Host ""
Write-Host " Summary " -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "  PASS: $pass" -ForegroundColor Green
Write-Host "  WARN: $warn" -ForegroundColor Yellow
Write-Host "  FAIL: $fail" -ForegroundColor Red

if ($fail -eq 0) {
    Write-Host ""
    Write-Host "Ready to teach." -ForegroundColor Green
    Write-Host "Next: .\start_sensei.ps1  ->  name the course, start the lecture, start listening." -ForegroundColor DarkGray
    exit 0
} else {
    Write-Host ""
    Write-Host "Fix the FAIL items before continuing:" -ForegroundColor Red
    foreach ($s in $failed_steps) { Write-Host "  - $s" -ForegroundColor Red }
    exit 1
}
