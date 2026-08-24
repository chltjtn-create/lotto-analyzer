<#
.SYNOPSIS
    Run the weekly Lotto update.

.DESCRIPTION
    The previous version refused to run on any day except Monday. That guard
    silently defeated the scheduler's catch-up behaviour: when the PC was off on
    a Monday, the AtStartup / StartWhenAvailable trigger fired the next day and
    was rejected, so that week's draw never got its own recommendation set.
    (This is why draws 1230 and 1234 have no recommendations.)

    This version always runs when invoked and lets the Python workflow decide
    whether a new draw exists. A once-per-day marker stops the startup trigger
    from producing duplicate runs and duplicate emails.
#>
param(
    [switch]$Force,
    [int]$TimeoutMinutes = 20
)

$ErrorActionPreference = "Stop"

$ProjectParent  = "D:\GoogleDrive"
$ProjectPackage = "D:\GoogleDrive\lotto_analyzer"
$LogDir         = Join-Path $ProjectPackage "logs"
$MarkerPath     = Join-Path $LogDir ".last_run_date"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Today     = Get-Date -Format "yyyy-MM-dd"
$StdoutLog = Join-Path $LogDir "weekly_task_$Timestamp.out.log"
$StderrLog = Join-Path $LogDir "weekly_task_$Timestamp.err.log"
$TraceLog  = Join-Path $LogDir "weekly_ps_$Timestamp.log"

# The PowerShell wrapper traces itself to its own file. If this file is missing
# after a run, the wrapper never started; if it exists but stops early, the line
# it stops on is the failure point.
function Trace([string]$Message) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $Message" |
        Out-File -FilePath $TraceLog -Encoding utf8 -Append
    Write-Host $Message
}

Trace "wrapper start (Force=$Force, timeout=${TimeoutMinutes}m)"

if (-not $Force -and (Test-Path $MarkerPath)) {
    $LastRun = (Get-Content $MarkerPath -Raw).Trim()
    if ($LastRun -eq $Today) {
        Trace "skipped: already ran today ($Today). Use -Force to run again."
        exit 0
    }
}

# Interpreter discovery lives in resolve_python.ps1 so it can be reused and
# debugged on its own. It verifies a candidate by importing the required
# packages, and writes every verdict to logs\python_probe.log.
$Resolver = Join-Path $PSScriptRoot "resolve_python.ps1"
if (-not (Test-Path $Resolver)) {
    Trace "ERROR: resolver script not found: $Resolver"
    exit 5
}

$Python = & $Resolver

if (-not $Python) {
    Trace "ERROR: no usable Python interpreter found. See logs\python_probe.log for every candidate tried."
    exit 3
}

Trace "interpreter: $Python"

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

Set-Location $ProjectParent
Trace "launching workflow"

# -u keeps stdout unbuffered so the log survives a hard kill.
$Process = Start-Process -FilePath $Python `
    -ArgumentList "-u", "-m", "lotto_analyzer.automation.run_weekly_update" `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError  $StderrLog `
    -NoNewWindow -PassThru

Trace "started pid $($Process.Id)"

$Finished = $Process.WaitForExit($TimeoutMinutes * 60 * 1000)

if (-not $Finished) {
    Trace "TIMEOUT after $TimeoutMinutes min. Killing pid $($Process.Id). Check weekly_run_*.log for the last completed step."
    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    exit 2
}

Trace "workflow exited with code $($Process.ExitCode)"

if ($Process.ExitCode -eq 0) {
    $Today | Out-File -FilePath $MarkerPath -Encoding utf8 -NoNewline
}

exit $Process.ExitCode
