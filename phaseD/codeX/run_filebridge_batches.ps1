$ErrorActionPreference='Stop'
$phaseXRoot='D:\论文集\phaseD'
$phaseXMatlab='C:\Program Files\MATLAB\R2023a\bin\matlab.exe'
foreach($phaseXStage in @('X1','X2')) {
 $phaseXCount=if($phaseXStage -eq 'X1'){240}else{140}
 $phaseXFolder=if($phaseXStage -eq 'X1'){'X1_duration'}else{'X2_frontend'}
 for($phaseXFirst=1;$phaseXFirst -le $phaseXCount;$phaseXFirst+=10) {
  $phaseXLast=[Math]::Min($phaseXFirst+9,$phaseXCount)
  $phaseXStamp=Join-Path $phaseXRoot "$phaseXFolder\short_batch_$('{0:d3}' -f $phaseXFirst)_$('{0:d3}' -f $phaseXLast).json"
  if(Test-Path -LiteralPath $phaseXStamp){continue}
  $phaseXExpression="addpath('D:\论文集\phaseD\code');addpath('D:\论文集\phaseD\codeX');run_phaseX_sim_filebridge('$phaseXStage',$phaseXFirst,$phaseXLast)"
  $phaseXLog=Join-Path $phaseXRoot "Y_compute\${phaseXStage}_filebridge_$phaseXFirst.log"
  & $phaseXMatlab -batch $phaseXExpression -logfile $phaseXLog
  $phaseXCode=$LASTEXITCODE
  if(!(Test-Path -LiteralPath $phaseXStamp)){throw "Incomplete $phaseXStage short batch $phaseXFirst-$phaseXLast, exit $phaseXCode. Preserve chunks and inspect before any resume."}
  if($phaseXCode -ne 0){Write-Output "Environment exit after completed batch: $phaseXStage $phaseXFirst-$phaseXLast, $phaseXCode"}
 }
 $phaseXExpression="addpath('D:\论文集\phaseD\code');addpath('D:\论文集\phaseD\codeX');run_phaseX_sim('$phaseXStage')"
 & $phaseXMatlab -batch $phaseXExpression -logfile (Join-Path $phaseXRoot "Y_compute\${phaseXStage}_assemble.log")
 if(!(Test-Path -LiteralPath (Join-Path $phaseXRoot "$phaseXFolder\${phaseXStage}_records.csv"))){throw "$phaseXStage final assembly incomplete"}
}
$phaseXExpression="addpath('D:\论文集\phaseD\code');addpath('D:\论文集\phaseD\codeX');run_phaseX3_real"
& $phaseXMatlab -batch $phaseXExpression -logfile (Join-Path $phaseXRoot 'Y_compute\X3_numeric.log')
if(!(Test-Path -LiteralPath (Join-Path $phaseXRoot 'X3_real\X3_run_config.json'))){throw 'X3 numeric stage incomplete'}
