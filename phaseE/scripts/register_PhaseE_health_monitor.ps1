$ErrorActionPreference = 'Stop'
$monitorTaskName = 'AcousticPaper_PhaseE_Health_5min'
$monitorAction = New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "D:\论文集\phaseE\scripts\run_PhaseE_health_check.ps1"'
$monitorTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval ([TimeSpan]::FromMinutes(5))
$monitorSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::FromMinutes(2)) -MultipleInstances IgnoreNew -Hidden
$monitorAccount = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$monitorPrincipal = New-ScheduledTaskPrincipal -UserId $monitorAccount -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $monitorTaskName -Action $monitorAction -Trigger $monitorTrigger -Settings $monitorSettings -Principal $monitorPrincipal -Description 'Every five minutes: read-only progress/process monitoring for the authorized paper experiments. Alert on exit, stop, stalled output, or validated C completion. Remove this task after B/C/D complete.' -Force | Out-Null
Start-ScheduledTask -TaskName $monitorTaskName
Get-ScheduledTask -TaskName $monitorTaskName | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName $monitorTaskName | Select-Object LastRunTime,NextRunTime,LastTaskResult
Export-ScheduledTask -TaskName $monitorTaskName | Set-Content -LiteralPath 'D:\论文集\phaseE\_health_monitor\scheduled_task.xml' -Encoding UTF8
