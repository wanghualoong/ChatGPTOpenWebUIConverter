param(
  [string]$PythonCmd = "py -3"
)

$ErrorActionPreference = "Stop"

Write-Host "[build] create/update venv"
if (!(Test-Path .venv\Scripts\python.exe)) {
  & $PythonCmd -m venv .venv
}

Write-Host "[build] install build dependencies"
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt

Write-Host "[build] build MSI"
.\.venv\Scripts\python.exe setup_windows.py bdist_msi

Write-Host "[done] MSI is under dist\\"
