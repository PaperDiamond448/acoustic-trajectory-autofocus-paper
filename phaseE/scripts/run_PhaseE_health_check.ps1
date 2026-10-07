$ErrorActionPreference = 'Stop'
$monitorRoot = 'D:\论文集\phaseE\_health_monitor'
$monitorArgs = @('-X','utf8','D:\论文集\phaseE\scripts\monitor_PhaseE_health.py','--once')
$monitorProcess = Start-Process -FilePath 'D:\python\python.exe' -ArgumentList $monitorArgs -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $monitorRoot 'scheduled.stdout.log') -RedirectStandardError (Join-Path $monitorRoot 'scheduled.stderr.log')
if ($monitorProcess.ExitCode -ne 0) { exit $monitorProcess.ExitCode }
$monitorSnapshot = Get-Content -LiteralPath (Join-Path $monitorRoot 'STATUS.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($monitorSnapshot.health -eq 'complete') {
    Unregister-ScheduledTask -TaskName 'AcousticPaper_PhaseE_Health_5min' -Confirm:$false -ErrorAction SilentlyContinue
}
