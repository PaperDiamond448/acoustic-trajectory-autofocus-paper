$ErrorActionPreference='Stop'
$PhaseXRoot='D:\论文集\phaseD';$PhaseXMatlab='C:\Program Files\MATLAB\R2023a\bin\matlab.exe'
foreach($PhaseXFolder in @('X1_duration','X2_frontend')){
 $PhaseXAudit=Join-Path $PhaseXRoot "$PhaseXFolder\SAVED_OUTPUTS_AUDIT.json"
 while(!(Test-Path -LiteralPath $PhaseXAudit)){Start-Sleep -Seconds 5}
 if((Get-Content -LiteralPath $PhaseXAudit -Raw | ConvertFrom-Json).status -ne 'PASS'){throw 'Simulation shard audit has not passed'}
}
foreach($PhaseXAudit in @('audit_phaseX3_saved','audit_worker_chunks','export_phaseX3_lofar')){
 & $PhaseXMatlab -batch "addpath('D:\论文集\phaseD\code');addpath('D:\论文集\phaseD\codeX');$PhaseXAudit" -logfile (Join-Path $PhaseXRoot "Y_compute\${PhaseXAudit}.log")
 if($LASTEXITCODE -ne 0){throw "Read-only audit or export environment exit: $PhaseXAudit; retain data, no optimizer may be rerun"}
}
foreach($PhaseXScript in @('analyze_phaseX.py','audit_real_metrics.py','audit_phaseX.py','supplement_phaseX_integrity.py','plot_phaseX.py','audit_phaseX_figures.py')){
 & python -X utf8 (Join-Path $PhaseXRoot "codeX\$PhaseXScript")
 if($LASTEXITCODE -ne 0){throw "Postprocess failed: $PhaseXScript; retain data and inspect"}
}
@{status='NUMERICAL_AND_AUTOMATED_QA_DONE_WAITING_FINAL_PNG_INSPECTION';timestamp=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PhaseXRoot 'Y_compute\FIGURES_READY.json') -Encoding utf8
Write-Output 'All automated checks complete; final PNG inspection/report/package remain.'
