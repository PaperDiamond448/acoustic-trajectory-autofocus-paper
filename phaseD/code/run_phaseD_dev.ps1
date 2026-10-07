$ErrorActionPreference='Stop'
$taskRoot='D:\论文集\phaseD'
$matlabExe='C:\Program Files\MATLAB\R2023a\bin\matlab.exe'
function Invoke-Stage($taskStage,$taskDelta,$taskRerun) {
    $taskCall="addpath('D:\论文集\phaseD\code'); run_phaseD_batch('$taskStage',$taskDelta,'$taskRerun')"
    & $matlabExe -batch $taskCall -logfile "$taskRoot\D_dev\${taskStage}_launcher.log"
    if ($LASTEXITCODE -ne 0) { throw "Stage $taskStage failed; no retry." }
}
function Invoke-Analysis($taskMode) {
    & python -X utf8 "$taskRoot\code\analyze_phaseD_dev.py" $taskMode
    if ($LASTEXITCODE -ne 0) { throw "Analysis $taskMode failed; no rule change." }
}
try {
    Invoke-Stage 'D1' 'NaN' ''
    Invoke-Analysis 'd1'
    $taskD1=Get-Content -LiteralPath "$taskRoot\D_dev\D1_DECISION.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $taskDelta=$taskD1.Delta_s.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    Invoke-Stage 'fixed' $taskDelta ''
    Invoke-Analysis 'fixed'
    $taskFixed=Get-Content -LiteralPath "$taskRoot\D_dev\D2_FIXED_DECISION.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $taskFixed.C0) {
        Invoke-Stage 'rerunA' $taskDelta ''
        Invoke-Analysis 'triggers'
        $taskTrigger=Get-Content -LiteralPath "$taskRoot\D_dev\D2_TRIGGER_DECISION.json" -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($taskTrigger.run_B) { Invoke-Stage 'rerunB' $taskDelta '' }
        Invoke-Analysis 'rerun'
        $taskRerun=Get-Content -LiteralPath "$taskRoot\D_dev\D2_RERUN_DECISION.json" -Raw -Encoding UTF8 | ConvertFrom-Json
        Invoke-Stage 'grid' $taskDelta $taskRerun.selected
    }
    Invoke-Analysis 'freeze'
    & python -X utf8 "$taskRoot\code\plot_phaseD_dev.py"
    if ($LASTEXITCODE -ne 0) { throw 'Figure export failed; scientific freeze retained.' }
    'STOP_POINT_1: Development completed. Confirmation remains unstarted.' | Set-Content -LiteralPath "$taskRoot\D_dev\STOP_POINT_1.txt" -Encoding UTF8
} catch {
    $_ | Out-String | Set-Content -LiteralPath "$taskRoot\D_dev\EXECUTION_ERROR.txt" -Encoding UTF8
    throw
}
