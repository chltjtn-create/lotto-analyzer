$ErrorActionPreference = "Stop"

$TaskName   = "LottoAnalyzerWeeklyUpdate"
$ScriptPath = "D:\GoogleDrive\lotto_analyzer\scripts\run_weekly_update.ps1"

if (-not (Test-Path $ScriptPath)) {
    throw "Weekly update script not found: $ScriptPath"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

$WeeklyTrigger  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:00AM
$StartupTrigger = New-ScheduledTaskTrigger -AtStartup

# ExecutionTimeLimit lowered from 1 hour to 30 minutes: the workflow finishes in
# well under a minute, so anything longer means a hung step. The script enforces
# its own 20-minute limit first so it can still write logs before being killed.
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger @($WeeklyTrigger, $StartupTrigger) `
    -Settings $Settings `
    -Description "Update Lotto DB, analyze results, and generate report every Monday (catches up on the next boot if the PC was off)." `
    -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
Write-Host "Manual test:"
Write-Host "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Force"
