<#
.SYNOPSIS
    Find a Python interpreter that can run the Lotto workflow.

.DESCRIPTION
    Candidates are never judged by their path. An earlier version rejected any
    path containing "WindowsApps" and thereby hid the only working interpreter on
    this machine - the Store-installed Python 3.11. The only reliable test is to
    run the interpreter and import what the workflow needs.

    Every candidate and its verdict is appended to logs\python_probe.log.
#>
param(
    [switch]$Refresh
)

$ErrorActionPreference = "Continue"

$LogDir    = "D:\GoogleDrive\lotto_analyzer\logs"
$CachePath = Join-Path $LogDir ".python_path"
$ProbeLog  = Join-Path $LogDir "python_probe.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Probe([string]$Message) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $Message" |
        Out-File -FilePath $ProbeLog -Encoding utf8 -Append
}

# Explicit override wins.
if ($env:LOTTO_PYTHON -and (Test-Path $env:LOTTO_PYTHON)) { return $env:LOTTO_PYTHON }

# Cached winner from a previous run. The cache is re-verified by running it:
# a path that merely exists is not proof it can be launched, which is how an
# ACL-locked Store path once got cached as the winner.
if (-not $Refresh -and (Test-Path $CachePath)) {
    $Cached = (Get-Content $CachePath -Raw).Trim()
    if ($Cached -and (Test-Path $Cached)) {
        $global:LASTEXITCODE = $null
        try {
            $Test = (& $Cached -c "import pandas, numpy, matplotlib, openpyxl; print('ok')" 2>&1) -join ' '
            if ($LASTEXITCODE -eq 0 -and $Test -match 'ok') { return $Cached }
        } catch { }
        Probe "cached interpreter no longer usable, rediscovering: $Cached"
    }
}

Probe "--- discovery start ---"

$Candidates = New-Object System.Collections.Generic.List[string]
function Add-Candidate([string]$Path) {
    if (-not $Path) { return }
    $Path = $Path.Trim()
    # C:\Program Files\WindowsApps is ACL-locked: launching a binary from there
    # fails with "Access is denied". Only the AppData alias can start Store Python.
    if ($Path -like "$env:ProgramFiles\WindowsApps\*") {
        Probe "skip (not executable, ACL-locked): $Path"
        return
    }
    if ($Path -and (Test-Path $Path) -and (-not $Candidates.Contains($Path))) {
        $Candidates.Add($Path)
        Probe "candidate: $Path"
    }
}

# PATH first. On this machine that yields
# %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe - the forwarding alias for the
# Store install. It is the only supported way to launch Store Python and is the
# entry point that worked until 2026-07-09.
foreach ($Name in @("python.exe", "python3.exe")) {
    try { foreach ($Line in (& where.exe $Name 2>$null)) { Add-Candidate $Line } } catch { }
}

# Regular installs.
foreach ($Glob in @(
    "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
    "$env:ProgramFiles\Python3*\python.exe",
    "C:\Python3*\python.exe",
    "$env:USERPROFILE\anaconda3\python.exe",
    "$env:USERPROFILE\miniconda3\python.exe"
)) {
    Get-ChildItem $Glob -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        ForEach-Object { Add-Candidate $_.FullName }
}

# Registry-registered installs.
foreach ($Root in @("HKCU:\SOFTWARE\Python\PythonCore", "HKLM:\SOFTWARE\Python\PythonCore")) {
    Get-ChildItem $Root -ErrorAction SilentlyContinue | ForEach-Object {
        $InstallPath = (Get-ItemProperty "$($_.PSPath)\InstallPath" -ErrorAction SilentlyContinue).'(default)'
        if ($InstallPath) { Add-Candidate (Join-Path $InstallPath "python.exe") }
    }
}

# The py launcher knows every registered install.
try {
    foreach ($Line in (& py -0p 2>$null)) {
        if ($Line -match '([A-Za-z]:\\[^\s].*python\.exe)') { Add-Candidate $Matches[1] }
    }
} catch { }

Probe "total candidates: $($Candidates.Count)"

$Check = "import pandas, numpy, matplotlib, openpyxl, sys; print(sys.version.split()[0])"

# A launch that is refused by the OS never sets $LASTEXITCODE, so a stale 0 from
# an earlier command used to be read as success. Reset it, catch the native
# launch exception, and require the output to actually look like a version.
foreach ($Candidate in $Candidates) {
    $global:LASTEXITCODE = $null
    try {
        $Output = (& $Candidate -c $Check 2>&1) -join ' '
    } catch {
        Probe "FAIL $Candidate  -> launch refused: $($_.Exception.Message)"
        continue
    }
    if ($LASTEXITCODE -eq 0 -and $Output -match '^\s*\d+\.\d+\.\d+') {
        Probe "OK   $Candidate  (python $Output)"
        $Candidate | Out-File -FilePath $CachePath -Encoding ascii -NoNewline
        Probe "selected: $Candidate"
        return $Candidate
    }
    Probe "FAIL $Candidate  (exit=$LASTEXITCODE) -> $Output"
}

# Nothing had every package. Report exactly what each one is missing so the fix
# is a single pip install instead of another round of guessing.
$Detail = "import sys, importlib.util" + [char]10 +
          "names = ('pandas','numpy','matplotlib','openpyxl')" + [char]10 +
          "missing = [n for n in names if importlib.util.find_spec(n) is None]" + [char]10 +
          "print(sys.version.split()[0], '| missing:', ','.join(missing) or 'none')"

foreach ($Candidate in $Candidates) {
    $global:LASTEXITCODE = $null
    try { $Output = (& $Candidate -c $Detail 2>&1) -join ' ' } catch { continue }
    if ($LASTEXITCODE -eq 0) { Probe "PARTIAL $Candidate -> $Output" }
}

Probe "no usable interpreter found"
return $null
