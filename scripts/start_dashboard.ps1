$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$localPython = Join-Path $projectRoot '.tools\python\python.exe'
if (Test-Path -LiteralPath $venvPython) {
    & $venvPython -m streamlit run dashboard/app.py
} elseif (Test-Path -LiteralPath $localPython) {
    & $localPython -m streamlit run dashboard/app.py
} else {
    python -m streamlit run dashboard/app.py
}
exit $LASTEXITCODE
