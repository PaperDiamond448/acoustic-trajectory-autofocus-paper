$ErrorActionPreference = 'Stop'
$shortBuildPath = Join-Path $PSScriptRoot '_build\build_docx.py'
& 'D:\python\python.exe' -X utf8 $shortBuildPath
if ($LASTEXITCODE -ne 0) { throw '精简稿生成失败，请查看前面的提示。' }
