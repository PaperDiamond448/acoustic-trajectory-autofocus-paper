$ErrorActionPreference='Stop'
$builder=Join-Path $PSScriptRoot '_build\build_docx.py'
& 'D:\python\python.exe' -X utf8 $builder --variant both
if ($LASTEXITCODE -ne 0) {throw "论文构建失败，退出码 $LASTEXITCODE"}
