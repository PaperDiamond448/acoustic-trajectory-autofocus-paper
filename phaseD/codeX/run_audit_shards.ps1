param([string]$PhaseXStage)
$ErrorActionPreference='Stop'
$PhaseXMatlab='C:\Program Files\MATLAB\R2023a\bin\matlab.exe';$PhaseXRoot='D:\论文集\phaseD'
if($PhaseXStage -eq 'X1'){$PhaseXCount=240;$PhaseXFolder='X1_duration'}elseif($PhaseXStage -eq 'X2'){$PhaseXCount=140;$PhaseXFolder='X2_frontend'}else{throw 'Unknown stage'}
for($PhaseXFirst=1;$PhaseXFirst -le $PhaseXCount;$PhaseXFirst+=10){
 $PhaseXLast=[Math]::Min($PhaseXFirst+9,$PhaseXCount)
 $PhaseXStamp=Join-Path $PhaseXRoot "$PhaseXFolder\qa_shards\shard_$('{0:d3}' -f $PhaseXFirst)_$('{0:d3}' -f $PhaseXLast)_AUDIT.json"
 if(Test-Path -LiteralPath $PhaseXStamp){$PhaseXProof=Get-Content -LiteralPath $PhaseXStamp -Raw | ConvertFrom-Json;if($PhaseXProof.status -ne 'PASS'){throw 'Existing shard is not PASS'};continue}
 & $PhaseXMatlab -batch "addpath('D:\论文集\phaseD\code');addpath('D:\论文集\phaseD\codeX');audit_phaseX_saved_shard('$PhaseXStage',$PhaseXFirst,$PhaseXLast)" -logfile (Join-Path $PhaseXRoot "Y_compute\${PhaseXStage}_audit_shard_${PhaseXFirst}.log")
 $PhaseXExit=$LASTEXITCODE
 if(!(Test-Path -LiteralPath $PhaseXStamp)){throw "Incomplete read-only shard $PhaseXStage $PhaseXFirst-$PhaseXLast; preserve numerical data, never optimize"}
 $PhaseXProof=Get-Content -LiteralPath $PhaseXStamp -Raw | ConvertFrom-Json
 if($PhaseXProof.status -ne 'PASS'){throw 'Shard has not passed'}
 Write-Output "$PhaseXStage audit shard $PhaseXFirst-$PhaseXLast PASS; native exit $PhaseXExit"
}
& python -X utf8 (Join-Path $PhaseXRoot 'codeX\merge_audit_shards.py') $PhaseXStage
if($LASTEXITCODE -ne 0){throw 'Shard coverage or merge failed'}
