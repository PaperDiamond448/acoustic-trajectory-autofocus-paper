$ErrorActionPreference='Stop'
$phaseXRoot='D:\论文集\phaseD';$phaseXMatlab='C:\Program Files\MATLAB\R2023a\bin\matlab.exe'
while(!(Test-Path -LiteralPath (Join-Path $phaseXRoot 'X3_real\X3_run_config.json'))){Start-Sleep -Seconds 5}
foreach($phaseXAudit in @("audit_phaseX_saved('X1')","audit_phaseX_saved('X2')",'audit_phaseX3_saved','audit_worker_chunks','export_phaseX3_lofar')) {
 $phaseXName=$phaseXAudit.Replace("'",'').Replace('(','_').Replace(')','')
 & $phaseXMatlab -batch "addpath('D:\论文集\phaseD\code');addpath('D:\论文集\phaseD\codeX');$phaseXAudit" -logfile (Join-Path $phaseXRoot "Y_compute\${phaseXName}.log")
 if($LASTEXITCODE -ne 0){throw "Read-only audit or export failed: $phaseXAudit; no optimizer may be rerun."}
}
foreach($phaseXScript in @('analyze_phaseX.py','audit_real_metrics.py','audit_phaseX.py','supplement_phaseX_integrity.py','plot_phaseX.py','audit_phaseX_figures.py')) {
 & python -X utf8 (Join-Path $phaseXRoot "codeX\$phaseXScript")
 if($LASTEXITCODE -ne 0){throw "Postprocess failed: $phaseXScript; retain all data and inspect output."}
}
@{status='NUMERICAL_AND_AUTOMATED_QA_DONE_WAITING_FINAL_PNG_INSPECTION';timestamp=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $phaseXRoot 'Y_compute\FIGURES_READY.json') -Encoding utf8
Write-Output 'All analyses and automatic audits done; final PNG inspection and report/package remain.'
